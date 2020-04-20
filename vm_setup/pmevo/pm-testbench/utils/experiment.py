# vim: et:ts=4:sw=4:fenc=utf-8

import random

from typing import *

from utils.architecture import *

import utils.jsonable as jsonable


class Experiment(jsonable.JSONable):
    def __init__(self, arch, iseq=[], result=None):
        super().__init__()
        if result is not None:
            assert "cycles" in result
        self.arch = arch
        self.iseq = iseq
        self.result = result
        self.rid = None
        self.other_results = []

    def items(self):
        return [(i, self.num_occurrences(i)) for i in self.get_distinct_insns()]

    def get_distinct_insns(self):
        return [i for i in Counter(self.iseq)]

    def num_occurrences(self, insn):
        return self.iseq.count(insn)

    def __str__(self):
        return "E_" + str(self.rid)

    def __repr__(self):
        return str(self.rid) + ": (" + str(self.iseq) + ", " + str(self.result) + ")"

    def get_name(self):
        return str(self.rid)

    def get_cycles(self):
        return self.result["cycles"]

    def get_result(self):
        return self.result

    def __eq__(self, other):
        if type(other) is type(self):
            return self.rid == other.rid
        return False

    def __hash__(self):
        return hash(self.rid)

    def from_json_dict(self, jsondict):
        assert(jsondict["kind"] == "Experiment")

        self.iseq = [ self.arch.insns[iname.replace(" ", "_")] for iname in jsondict["iseq"] ]

        self.result = jsondict["result"]
        if self.result is not None:
            self.result["cycles"] = float(self.result["cycles"])

        if "other_results" in jsondict:
            self.other_results = jsondict["other_results"]

    def to_json_dict(self):
        res = dict()
        res["kind"] = "Experiment"
        res["iseq"] = [ i.name for i in self.iseq ]
        res["result"] = self.result
        if self.other_results is not None and len(self.other_results) != 0:
            res["other_results"] = self.other_results
        return res

class ExperimentList(jsonable.JSONable):
    def __init__(self, arch=None):
        super().__init__()
        self.arch = arch
        self.exps = []
        self.experiment_id = 0
        self.modifiable = True

    def check_modifiable(self):
        if not self.modifiable:
            raise RuntimeError("Trying to modify unmodifiable ExperimentList!")

    def __iter__(self):
        return iter(self.exps)

    def split_randomly(self, ratio):
        """
            Create two ExperimentList "views" of this list, split randomly,
            with round(len(self.exps) * ratio) elements in the first view and
            len(self.exps) - round(len(self.exps) * ratio) elements in the
            second view.
        """
        all_exps = self.exps.copy()
        random.shuffle(all_exps)

        inA = round(len(all_exps) * ratio)

        resA = ExperimentList(self.arch)
        resA.exps.extend(all_exps[:inA-1])
        resA.modifiable = False

        resB = ExperimentList(self.arch)
        resB.exps.extend(all_exps[inA-1:])
        resB.modifiable = False

        return (resA, resB)


    def clear(self):
        self.check_modifiable()
        self.exps.clear()

    def insert_exp(self, e):
        self.check_modifiable()
        e.rid = self.experiment_id
        self.experiment_id += 1
        self.exps.append(e)

    def create_exp(self, ilist):
        self.check_modifiable()
        new_exp = Experiment(self.arch, ilist)
        self.insert_exp(new_exp)
        return new_exp

    def insert_random_exp(self, num_insns):
        self.check_modifiable()
        assert(num_insns > 0)
        iseq = []
        I = self.arch.insn_list()
        for x in range(num_insns):
            insn = I[random.randrange(len(I))]
            iseq.append(insn)

        res = Experiment(self.arch, iseq)
        self.insert_exp(res)

        return res

    def insert_random_exps(self, num_exps, max_num_insns):
        self.check_modifiable()
        for i in range(num_exps):
            num_insns = random.randrange(1, max_num_insns + 1)
            self.insert_random_exp(num_insns)

    def from_json_dict(self, jsondict):
        self.check_modifiable()
        assert(jsondict["kind"] == "ExperimentList")
        if self.arch is None:
            self.arch = Architecture()
            self.arch.from_json_dict(jsondict["arch"])
        else:
            self.arch.verify_json_dict(jsondict["arch"])

        for edict in jsondict["exps"]:
            e = Experiment(self.arch)
            e.from_json_dict(edict)
            self.insert_exp(e)

    def to_json_dict(self):
        res = dict()
        res["kind"] = "ExperimentList"
        arch_dict = self.arch.to_json_dict()
        res_dict = dict()
        for k, v in arch_dict.items():
            res_dict[k] = jsonable.mark_noindent(v)
        res["arch"] = res_dict

        res["exps"] = [ jsonable.mark_noindent(e.to_json_dict()) for e in self.exps ]

        return res

