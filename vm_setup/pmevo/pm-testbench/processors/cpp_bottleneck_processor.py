# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import *

from utils.architecture import Architecture, Insn, Port
from utils.experiment import Experiment
from .sim_processor import SimProcessor

import sys
import os

cppfastproc_path = os.path.join(os.path.dirname(__file__), '../cppfastproc/build')
sys.path.append(cppfastproc_path)

has_cppfastproc = True

try:
    from cppfastproc import FP
except ImportError:
    has_cppfastproc = False

assert has_cppfastproc, "Custom module for the fast bottleneck simulator could not be found!"

class CPPBottleneckProcessor(SimProcessor):
    """ Fast, but not so portable simulation processor implementation, uses
        external C++ code.
    """
    def __init__(self, mapping: Mapping):
        super().__init__(mapping)
        self.fp = FP(len(self.arch.port_list()))

    def get_description(self):
        return "simulation processor using the bottleneck algorithm (C++)"

    def cycles_for_weights(self, weights):
        self.fp.clear()

        for u, v in weights.items():
            self.fp.add(u, v)

        return self.fp.compute()

