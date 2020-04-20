# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod
from typing import *
import itertools
import json
import os
import sys
import textwrap
from subprocess import Popen, PIPE
from pathlib import Path
from collections import defaultdict

from processors.processor import Processor
from utils.experiment import ExperimentList
from utils.mapping import Mapping

class Inferrer(ABC):
    @abstractmethod
    def infer(self, exps: ExperimentList) -> Mapping:
        pass

    @staticmethod
    def from_config(config):
        cls = Inferrer.class_for_name(config['inferrer'])
        return cls(config=config)

    @staticmethod
    def class_for_name(name: str):
        lname = name.lower()
        lname = lname.replace("_", "")
        if lname.endswith("inferrer"):
            lname = lname[:-len("inferrer")]
        elif lname == "pmevo":
            return EvoAlgoWrapper
        # insert new inferrers here
        elif lname.startswith("partitioning"):
            base_cls = Inferrer.class_for_name(lname[len("partitioning"):])
            return base_cls.make_partitioning()
        else:
            raise RuntimeError("Unknown Inferrer: {}".format(name))

    @classmethod
    def make_partitioning(cls):
        """ Create an Inferrer that performs inference on a restricted set of
            instructions and experiments. The instructions are restricted to the
            representatives of a partitioning into sets of instructions that
            are indistinguishable wrt. the given set of experiments.
            Experiments are expected to include a singleton experiment for each
            instruction and exhaustive experiments for all pairs of instructions.
        """
        from utils.partition_insns import compute_representatives, restrict_elist, generalize_mapping

        class PartitioningInferrer(cls):
            @staticmethod
            def get_default_config():
                config = cls.get_default_config()
                config["equivalence_epsilon"] = 0.1
                return config

            def __init__(self, config=None):
                super().__init__(config)
                if config is not None:
                    self.epsilon = config["equivalence_epsilon"]

            def infer(self, exps):
                old_exps = exps
                old_arch = old_exps.arch

                singleton_exps = ExperimentList(exps.arch)
                singleton_exps.exps = [e for e in exps if len(e.iseq) == 1]

                complex_exps = ExperimentList(exps.arch)
                complex_exps.exps = [e for e in exps if len(e.iseq) > 1]

                reps, insn_to_rep = compute_representatives(complex_exps, singleton_exps, epsilon=self.epsilon)

                exps = restrict_elist(exps, reps)
                print("Restricted input to {insns} out of {old_insns} instructions and {exps} out of {old_exps} experiments.".format(
                        insns=len(reps),
                        old_insns=len(old_arch.insns.keys()),
                        exps=len(exps.exps),
                        old_exps=len(old_exps.exps)
                    ))

                mapping = super().infer(exps)

                mapping = generalize_mapping(old_arch, mapping, insn_to_rep)

                return mapping
        return PartitioningInferrer


class EvoAlgoWrapper(Inferrer):
    """
        An Inferrer that wraps the C++ part of PMEvo for convenient use
    """
    def __init__(self, config=None):
        self.bin_path = os.path.expandvars(os.path.expanduser(config["bin_path"]))
        self.config_path = os.path.expandvars(os.path.expanduser(config["config_path"]))
        self.journal_path = "/tmp/pmtestbench_tmp_evo_journal.log"

        self.cmd = [
                # "echo",
                self.bin_path,                    # call the genetic algorithm binary
                "-c{}".format(self.config_path),  # use the specified config for the genetic algorithm
                "-i",                             # let the genetic algorithm read experiments from stdin
                "-j",                             # let it also print the resulting mapping as json to stdout
                "-n1",                            # print only the best mapping
                "-x{}".format(self.journal_path), # do some logging
                ]

    def infer(self, exps):
        singleton_exps = ExperimentList(exps.arch)
        singleton_exps.exps = [e for e in exps if len(e.iseq) == 1]
        singleton_elist_path = "/tmp/pmtestbench_tmp_singleton.exps"
        singleton_elist_str = export_explist(singleton_exps)
        with open(singleton_elist_path, "w") as ef:
            print(singleton_elist_str, file=ef)

        # transform exps into string
        expstr = export_explist(exps)
        # print(expstr)

        # start binary with config and exps
        cmd = self.cmd + ["-q{}".format(len(exps.arch.ports)), "-e{}".format(singleton_elist_path)]
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        outs, errs = p.communicate(input=expstr.encode('utf-8'))
        out_str = outs.decode('utf-8')
        err_str = errs.decode('utf-8')
        retval = p.returncode

        # print("output on stdout:", file=sys.stderr)
        # print(textwrap.indent(out_str, "  "), file=sys.stderr)
        print("output on stderr:", file=sys.stderr)
        print(textwrap.indent(err_str, "  "), file=sys.stderr)

        if retval != 0:
            print("Evolutionary algorithm binary returned with non-zero return code: {}!".format(retval), file=sys.stderr)
            print("Command: {}".format(" ".join(cmd)))
            print("output on stdout:", file=sys.stderr)
            print(textwrap.indent(out_str, "  "), file=sys.stderr)
            # print("output on stderr:", file=sys.stderr)
            # print(textwrap.indent(err_str, "  "), file=sys.stderr)
            return None

        # read mapping
        mapping = Mapping.read_from_json_str(out_str, arch=exps.arch)

        return mapping


def export_explist(elist):
    indent = " " * 4
    result = ""
    result += "architecture:\n"
    result += indent + "instructions:\n"
    arch = elist.arch
    for i in arch.insn_list():
        result += indent * 2 + "{}\n".format(i.name)
    result += indent + "ports: {}\n\n".format(len(arch.port_list()))
    for e in elist:
        result += "experiment:\n"
        result += indent + "instructions:\n"
        for i in e.iseq:
            result += indent * 2 + "{}\n".format(i.name)
        result += indent + "cycles: {}\n".format(e.get_cycles())
        result += "\n"
    return result

def export_mapping(mapping):
    indent = " " * 4
    result = "mapping:\n"
    for i, uops in mapping.assignment.items():
        result += "{}:\n".format(i.name)
        uop_map = defaultdict(lambda:0)
        for u in uops:
            rep = ""
            for p in sorted(u, key=lambda x: int(x.name)):
                num = int(p.name)
                assert 0 <= num and num < 26
                rep += chr(ord("A") + num)
            uop_map[rep] += 1

        for u, n in uop_map.items():
            if n <= 0:
                continue
            result += indent + "{}: {}\n".format(u, n)
        result += "\n"
    return result

def evaluateExperiments(bin_path, m, exps, num_repetitions):
    mapping_path = "/tmp/pmtestbench_tmp.pmap"
    mapping_str = export_mapping(m)
    with open(mapping_path, "w") as mf:
        print(mapping_str, file=mf)

    elist_path = "/tmp/pmtestbench_tmp.exps"
    elist_str = export_explist(exps)
    with open(elist_path, "w") as ef:
        print(elist_str, file=ef)

    cmd = [
            # "echo",
            bin_path,
            "-m{}".format(mapping_path),
            "-t{}".format(num_repetitions),
            elist_path,
        ]
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    outs, errs = p.communicate()
    out_str = outs.decode('utf-8')
    err_str = errs.decode('utf-8')
    retval = p.returncode

    # print(out_str)
    # print(err_str)

    if retval != 0:
        print("Genetic algorithm binary returned with non-zero return code!", file=sys.stderr)
        print("output on stdout:", file=sys.stderr)
        print(textwrap.indent(out_str, "  "), file=sys.stderr)
        print("output on stderr:", file=sys.stderr)
        print(textwrap.indent(err_str, "  "), file=sys.stderr)
    assert retval == 0

    result = json.loads(err_str)
    return result["secs_per_exp"]
