# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod
from typing import *

from utils.architecture import Architecture, Insn, Port
from .processor import Processor

import rpyc


def unwrap_netref(o):
    if isinstance(o, dict):
        return { unwrap_netref(k): unwrap_netref(o[k]) for k in o }
    elif isinstance(o, list):
        return [ unwrap_netref(v) for v in o]
    else:
        return o

class RemoteProcessor(Processor):
    """
        Implementation of the processor interface that executes the experiments
        on a server running on a remote machine.
    """
    def __init__(self, hostname, port=42424, sslpath=".", filter_list=[], request_timeout=30):
        self.hostname = hostname
        self.port = port
        self.keyfile = sslpath + "/key.pem"
        self.certfile = sslpath + "/cert.pem"
        self.request_timeout = request_timeout
        c = self.conn()

        insn_ids = c.root.get_insns()

        if len(filter_list) > 0:
            # ignore all whitespaces in input
            insn_ids = [i for i in insn_ids if "".join(str(i).split()) in filter_list]

        self.insn_dict = dict()

        self.arch = Architecture()
        for iid in insn_ids:
            insn = self.arch.add_insn(str(iid))
            self.insn_dict[insn] = iid

        num_ports = c.root.get_num_ports()
        self.arch.add_number_of_ports(num_ports)

        remote_description = c.root.get_description()
        self.remote_description = remote_description

        c.close()

    def conn(self):
        return rpyc.ssl_connect(
                self.hostname,
                port=self.port,
                keyfile=self.keyfile,
                certfile=self.certfile,
                config={'sync_request_timeout': self.request_timeout})

    def get_description(self):
        return "remote processor wrapping a {} from {}:{}".format(
                self.remote_description, self.hostname, self.port)

    def gen_code(self, iseq, **kwargs):
        exp = [self.insn_dict[i] for i in iseq]
        c = self.conn()
        remote_res = c.root.gen_code(exp, **kwargs)
        res = unwrap_netref(remote_res)
        return res

    def execute(self, iseq: List[Insn], **kwargs) -> Dict[str, float]:
        exp = [self.insn_dict[i] for i in iseq]
        c = self.conn()
        try:
            remote_res = c.root.run_experiment(exp, **kwargs)
            # unwrap netref before closing the connection
            res = unwrap_netref(remote_res)
        except rpyc.AsyncResultTimeout:
            res = {'cycles': None, 'error_cause': 'connection timeout'}
        finally:
            c.close()
        return res

    def get_arch(self):
        return self.arch

