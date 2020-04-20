# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod
from collections import defaultdict
from fractions import *
from typing import *

from utils.architecture import Architecture, Insn, Port
from utils.experiment import Experiment
from .sim_processor import SimProcessor

def popcount(n):
    """ Return the number of 1s in the binary representation of the number n.
    """
    return bin(n).count("1")

class BottleneckProcessor(SimProcessor):
    """ Slow, but most portable simulation processor implementation, fully
        self-contained python.
    """
    def __init__(self, mapping: Mapping):
        super().__init__(mapping)

    def get_description(self):
        return "simulation processor using the bottleneck algorithm (pure python)"

    def cycles_for_weights(self, weights):
        max_val = Fraction(0)
        for q in range(1, self.max_uop + 1):
            val = 0
            for u, w in weights.items():
                if (~q & u) == 0: # all ports of u are contained in q
                    val += w
            val = Fraction(val) / popcount(q)
            max_val = max(max_val, val)
        return float(max_val)

