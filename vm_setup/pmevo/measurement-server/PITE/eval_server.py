# vim: et:ts=4:sw=4:fenc=utf-8

# This script uses the RPyC library for remote procedure calls
import rpyc
import os.path
import sys


class BenchmarkingService(rpyc.Service):
    def __init__(self, lleval):
        self.lowleveleval = lleval

    def on_connect(self, conn):
        # code that runs when a connection is created
        # (to init the service, if needed)
        print("Opened connection")

    def on_disconnect(self, conn):
        # code that runs after the connection has already closed
        # (to finalize the service, if needed)
        print("Closed connection")

    def exposed_get_insns(self):
        print("  handling request for instruction list")
        return self.lowleveleval.get_insns()

    def exposed_get_num_ports(self):
        print("  handling request for port number")
        return self.lowleveleval.get_num_ports()

    def exposed_run_experiment(self, insnseq, **kwargs):
        print("  handling request for running experiment ", insnseq)
        return self.lowleveleval.run_experiment(insnseq, **kwargs)

    def exposed_gen_code(self, insnseq, **kwargs):
        print("  handling request for generating code for experiment ", insnseq)
        return self.lowleveleval.gen_code(insnseq, **kwargs)

    def exposed_get_description(self):
        print("  handling request for human-readable description")
        return self.lowleveleval.get_description()

class SSLInfo:
    def __init__(self, folder):
        self.sslfolder = folder
        self.certfile = os.path.join(folder, "cert.pem")
        self.keyfile = os.path.join(folder, "key.pem")
        self.cafile = os.path.join(folder, "ca_file.pem")

        def check_file(f, desc):
            if not os.path.isfile(f):
                print("{} missing!".format(desc), file=sys.stderr)
                sys.exit(1)

        check_file(self.certfile, "SSL certificate file")
        check_file(self.keyfile, "SSL keyfile")
        check_file(self.cafile, "SSL CA file")


def generateSSL(sslpath):
    """
    This function generates the ssl certificates necessary for safe connection
    between server and client.
    The ssl configuration is only created if it is not yet existing.
    """
    import os
    import subprocess
    from shutil import copyfile
    if not os.path.isdir(sslpath):
        os.mkdir(sslpath)
        certfile = os.path.join(sslpath, "cert.pem")
        keyfile = os.path.join(sslpath, "key.pem")
        cafile = os.path.join(sslpath, "ca_file.pem")

        print('Creating self signed SSL certificate for remote connections...')
        subprocess.call([
            'openssl',
            'req', '-new',      # request a new openssl certificate
            '-x509',            # Output a x509 structure instead of a cert request (Required by some CA's)
            '-days', '3650',    # the certificate is valid for 10 years
            '-nodes',           # don't encrypt the output key
            '-out', certfile,   # output the certificate here...
            '-keyout', keyfile, # ...and the key file here
        ])
        copyfile(certfile, cafile)
        print('Done creating certificate. Consider adding authorized clients to {}'.format(cafile))
    return SSLInfo(sslpath)


def start_server(lleval, sslinfo, port=42424):
    from rpyc.utils.authenticators import SSLAuthenticator
    from rpyc.utils.server import ThreadedServer

    service = BenchmarkingService(lleval)

    authenticator = SSLAuthenticator(
            keyfile=sslinfo.keyfile,
            certfile=sslinfo.certfile,
            ca_certs=sslinfo.cafile
        )
    t = ThreadedServer(service, port=port, authenticator=authenticator)
    t.start()

class FrequencySetter:
    def __init__(self, settings, core=None):
        if core is None:
            core = settings.core
        assert core is not None

        self.governor_file_path = settings.scaling_gov.format(core=core)
        self.max_freq_file_path = settings.scaling_max_freq.format(core=core)
        self.min_freq_file_path = settings.scaling_min_freq.format(core=core)

        self.prev_governor = self.read(self.governor_file_path)
        self.prev_max_freq = self.read(self.max_freq_file_path)
        self.prev_min_freq = self.read(self.min_freq_file_path)

        self.write(self.governor_file_path, "performance")
        self.write(self.max_freq_file_path, self.prev_max_freq)
        # set new min freq to max freq (order matters!)
        self.write(self.min_freq_file_path, self.prev_max_freq)

    def read(self, fn):
        with open(fn, "r") as f:
            return f.readline()

    def write(self, fn, val):
        with open(fn, "w") as f:
            return f.write(val)

    def __del__(self):
        # Do some cleanup afterwards
        self.write(self.governor_file_path, self.prev_governor)
        self.write(self.max_freq_file_path, self.prev_max_freq)
        self.write(self.min_freq_file_path, self.prev_min_freq)


def start(args):
    from PITE.settings import Settings
    from PITE.processor_benchmarking import PITELLEval
    from PITE.isa import create_ISA
    from PITE.machine_params import get_machine_dependent_params

    sslinfo = generateSSL(args.sslpath)

    # generate settings
    settings = Settings()
    settings.preciseStart = args.precise
    settings.newSU = args.newSU
    settings.core = args.core

    # use an output directory determined by the port so that multiple instances
    # can run without conflict
    settings.output_dir = "/tmp/pite_{}/".format(args.port)

    if not os.path.isdir(settings.output_dir):
        os.mkdir(settings.output_dir)

    # read in architecture information
    if args.iaca:
        isa = create_ISA(settings, "IACAx86_64")
    elif args.ithemal:
        isa = create_ISA(settings, "Ithemalx86_64")
    else:
        isa = create_ISA(settings, args.isa)

    simulated = isa.is_simulated()
    settings.no_root = simulated

    # set core frequency, preserved until this object is destroyed
    if settings.no_root:
        freq_setter = None
    else:
        freq_setter = FrequencySetter(settings)

    # collect machine dependent information and add to settings
    if not simulated:
        get_machine_dependent_params(settings, isa)
    else:
        settings.num_total_dynamic_insns = 10
        settings.num_insns_per_iteration = 10
        settings.default_num_repetitions = 1

    settings.finalize()

    # start the actual server
    lleval = PITELLEval(settings, isa, num_ports=args.numports, freq_setter=freq_setter)
    print("Starting server on port {}".format(args.port))
    start_server(lleval, sslinfo=sslinfo, port=args.port)

