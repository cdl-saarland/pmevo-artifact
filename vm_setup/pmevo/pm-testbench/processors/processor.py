# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod
from typing import *
from time import sleep
import random

from utils.architecture import Architecture, Insn, Port
from utils.experiment import Experiment, ExperimentList

class Processor(ABC):
    @staticmethod
    def class_for_name(name: str):
        lname = name.lower()
        lname = name.replace("_", "")
        if lname.endswith("processor"):
            lname = lname[:-len("processor")]
        if lname == "bottleneck":
            import processors.bottleneck_processor
            return processors.bottleneck_processor.BottleneckProcessor
        elif lname == "cppbottleneck":
            import processors.cpp_bottleneck_processor
            return processors.cpp_bottleneck_processor.CPPBottleneckProcessor
        elif lname == "lp":
            import processors.lp_processor
            return processors.lp_processor.LPProcessor
        # TODO insert new processors
        elif lname.startswith("delayed"):
            base_cls = Processor.class_for_name(lname[len("delayed"):])
            return base_cls.make_delayed()
        elif lname.startswith("jittered"):
            base_cls = Processor.class_for_name(lname[len("jittered"):])
            return base_cls.make_jittered()
        else:
            raise RuntimeError("Unknown processor: {}".format(name))

    @staticmethod
    def get_default_cls(prefix=""):
        return Processor.class_for_name(prefix+"bottleneckprocessor")

    @abstractmethod
    def get_arch(self):
        pass

    @abstractmethod
    def get_description(self):
        """ Get a human-readable description of the processor.
        """
        pass

    def execute(self, iseq: List[Insn]) -> Dict[str, float]:
        """ Return a dictionary with execution results for the list iseq of
            instructions. The result has to contain at least a float entry for
            the key 'cycles'.
        """
        res = self.get_cycles(iseq)
        return { 'cycles': res }

    def get_cycles(self, iseq: List[Insn]) -> float:
        """ Return the number of cycles required to execute the list iseq of
            instructions.
        """
        res = self.execute(iseq)
        return res['cycles']

    def eval(self, exp: Experiment):
        """ Evaluate the given experiment and insert the results.
        """
        res = self.execute(exp.iseq)
        exp.result = res

    def eval_list(self, exps: ExperimentList):
        """ Evaluate the given ExperimentList and insert the results.
        """
        for e in exps:
            self.eval(e)


    @classmethod
    def make_delayed(cls):
        class DelayedProcessor(cls):
            def __init__(self, *args, **kwargs):
                if "delay" in kwargs:
                    self.delay = kwargs["delay"]
                    del kwargs["delay"]
                else:
                    self.delay = 1000
                super().__init__(*args, **kwargs)

            def get_description(self):
                super_desc = super().get_description()
                res = "delayed processor wrapping a ({}) with a delay of {} ms".format(super_desc, self.delay)
                return res

            def execute(self, iseq: List[Insn]) -> Dict[str, float]:
                sleep(self.delay / 1000)
                return super().execute(iseq)

            def get_cycles(self, iseq: List[Insn]) -> float:
                sleep(self.delay / 1000)
                return super().get_cycles(iseq)

        return DelayedProcessor

    @classmethod
    def make_jittered(cls):
        class JitteredProcessor(cls):
            def __init__(self, *args, **kwargs):
                if "jitter" in kwargs:
                    self.jitter = kwargs["jitter"]
                    del kwargs["jitter"]
                else:
                    self.jitter = 0.1
                super().__init__(*args, **kwargs)

            def get_description(self):
                super_desc = super().get_description()
                res = "jittered processor wrapping a ({}) with a jitter of {} cycles".format(super_desc, self.jitter)
                return res

            def execute(self, iseq: List[Insn]) -> Dict[str, float]:
                res = super().execute(iseq)
                jitter = random.uniform(-self.jitter, self.jitter)
                res["cycles"] += jitter
                return res

            def get_cycles(self, iseq: List[Insn]) -> float:
                res = super().get_cycles(iseq)
                jitter = random.uniform(-self.jitter, self.jitter)
                res += jitter
                return res

        return JitteredProcessor

