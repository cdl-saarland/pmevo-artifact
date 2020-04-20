# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod
from fractions import Fraction
from typing import List

from utils.pmdefs import Insn, Port


class Evaluator(ABC):
    @abstractmethod
    def getInsns(self) -> List[Insn]:
        pass

    @abstractmethod
    def getPorts(self) -> List[Port]:
        pass

    @abstractmethod
    def runExperiment(self, iseq: List[Insn], loop_length=None, insnNbr=None) -> Fraction:
        pass
