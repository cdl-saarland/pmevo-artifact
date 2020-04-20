# vim: et:ts=4:sw=4:fenc=utf-8

from utils.evaluator import Evaluator
from utils.pmdefs import Insn, Port
from typing import List

import rpyc


class RemoteEvaluator(Evaluator):
    def __init__(self, hostname, port, sslpath, num_uops=4, filter_list=[]):
        # TODO move num_uops to remote call?
        self.hostname = hostname
        self.port = port
        self.keyfile = sslpath + "/key.pem"
        self.certfile = sslpath + "/cert.pem"
        c = self.conn()

        insn_ids = c.root.get_insns()

        if len(filter_list) > 0:
            # ignore all whitespaces in input
            insn_ids = [i for i in insn_ids if "".join(str(i).split()) in filter_list]

        self.insn_dict = {Insn(str(iid), num_uops): iid for iid in insn_ids}
        self.insns = list(self.insn_dict.keys())

        num_ports = c.root.get_num_ports()
        self.ports = [Port(str(i)) for i in range(num_ports)]

        c.close()

    def conn(self):
        return rpyc.ssl_connect(self.hostname,
                                port=self.port,
                                keyfile=self.keyfile,
                                certfile=self.certfile)

    def getInsns(self) -> List[Insn]:
        return list(self.insns)

    def getPorts(self) -> List[Port]:
        return list(self.ports)

    def runExperiment(self, iseq: List[Insn], loop_length=None, insnNbr=None) -> List[float]:
        c = self.conn()
        exp = [self.insn_dict[i] for i in iseq]
        assert (exp)
        async_func = rpyc.async_(c.root.run_experiment)
        res = async_func(exp, loop_length, insnNbr)
        if res.ready:
            res = res.value
            c.close()
            return res
        res.wait()
        res = res.value
        # res is a list of 2 floats:
        # the first one is the overall execution time of the testcase
        # the second one is the instruction throughput of the experiment
        floats = {iid: float(res[iid]) for iid in res}
        c.close()
        return floats
