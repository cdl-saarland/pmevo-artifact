# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import *

from utils.architecture import Architecture, Insn, Port
from utils.experiment import Experiment
from utils.mapping import *

from .processor import Processor

class SimProcessor(Processor):
    def __init__(self, mapping: Mapping):
        self.arch = mapping.arch
        self.mapping = mapping

        all_ports = self.arch.port_list()
        self.port2idx = dict()
        for x, p in enumerate(all_ports):
            self.port2idx[p] = x

        self.max_uop = self.uop2bv(all_ports)

    def uop2bv(self, u):
        """ Compute a bitvector representing the list p of ports.
        """
        res = 0
        for p in u:
            res += (1 << self.port2idx[p])
        return res

    def get_arch(self):
        return self.arch

    def get_cycles(self, iseq: List[Insn]) -> float:
        weights = defaultdict(lambda : 0)
        if isinstance(self.mapping, Mapping3):
            for i in iseq:
                for u in self.mapping.assignment[i]:
                    weights[self.uop2bv(u)] += 1
        elif isinstance(self.mapping, Mapping2):
            for i in iseq:
                weights[self.uop2bv(self.mapping.assignment[i])] += 1
        else:
            raise NotImplementedError("get_cycles")
        return self.cycles_for_weights(weights)

    @abstractmethod
    def cycles_for_weights(self, weights):
        """ Compute the number of cycles required to execute the experiment
            represented by the dictionary weights that maps operations that can
            be executed on ports to the number how often they occur in the
            experiment.
        """
        pass


