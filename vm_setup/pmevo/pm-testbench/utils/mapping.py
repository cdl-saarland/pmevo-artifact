# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod
import random
from typing import *
import json

from utils.architecture import Architecture
import utils.jsonable as jsonable

class Mapping(jsonable.JSONable):
    """ Abstract base class for port mappings.
    """
    def __init__(self):
        super().__init__()

    @staticmethod
    def read_from_json_dict(jsondict, arch: Architecture = None):
        assert(jsondict["kind"] in ["Mapping2", "Mapping3"])

        if arch is None:
            arch = Architecture()
            arch.from_json_dict(jsondict["arch"])
        else:
            arch.verify_json_dict(jsondict["arch"])

        if jsondict["kind"] == "Mapping3":
            res = Mapping3(arch)
            res.from_json_dict(jsondict)
            return res

        if jsondict["kind"] == "Mapping2":
            res = Mapping2(arch)
            res.from_json_dict(jsondict)
            return res

        raise NotImplementedError("read_from_json")

    @staticmethod
    def read_from_json(infile, arch: Architecture = None):
        jsondict = json.load(infile)
        return Mapping.read_from_json_dict(jsondict, arch)

    @staticmethod
    def read_from_json_str(instr, arch: Architecture = None):
        jsondict = json.loads(instr)
        return Mapping.read_from_json_dict(jsondict, arch)


class Mapping3(Mapping):
    """ Class representing port mappings where instructions are decomposed into
        uops that can be executed on ports.
    """
    def __init__(self, arch: Architecture):
        super().__init__()

        self.arch = arch

        # an assignment from instructions to lists of lists of ports
        self.assignment = { i: [] for i in  self.arch.insn_list() }

    def __getitem__(self, key):
        assert key in self.assignment
        return self.assignment[key]

    def __repr__(self):
        res = "Mapping3(arch={}, assignment={})".format(repr(self.arch), repr(self.assignment))
        return res

    def to_json_dict(self):
        res = dict()
        res["kind"] = "Mapping3"

        arch_dict = self.arch.to_json_dict()
        res_dict = dict()
        for k, v in arch_dict.items():
            res_dict[k] = jsonable.mark_noindent(v)
        res["arch"] = res_dict

        assignment_dict = dict()
        for i, us in self.assignment.items():
            curr_uops = []
            for ps in us:
                curr_uops.append([p.name for p in ps])
            assignment_dict[i.name] = jsonable.mark_noindent(curr_uops)

        res["assignment"] = assignment_dict

        return res

    def from_json_dict(self, jsondict):
        assert(jsondict["kind"] == "Mapping3")
        arch = self.arch
        assignment_dict = jsondict["assignment"]
        for i, us in assignment_dict.items():
            insn = arch.insns[i]
            curr_uops = []
            for ps in us:
                curr_uops.append([arch.ports[p] for p in ps])
            self.assignment[insn] = curr_uops


    @classmethod
    def from_random(cls, arch: Architecture, num_uops_per_insn: int):
        """ Generate a new random Mapping for the given architecture with at
            most num_uops_per_insn uops per instruction (not necessarily
            distinct).
        """
        return cls.from_random_with_core(arch, num_uops_per_insn=num_uops_per_insn, core_ratio=1.0)

    @classmethod
    def from_random_with_core(cls, arch: Architecture, num_uops_per_insn: int, core_ratio):
        """ Generate a new random Mapping for the given architecture with at
            most num_uops_per_insn uops per instruction (not necessarily
            distinct).
            Only core_ratio * number of instructions many instructions are
            generated randomly, the others are composed of core instructions.
        """
        assert(0.0 <= core_ratio and core_ratio <= 1.0)

        res = cls(arch)

        I = arch.insn_list()
        P = arch.port_list()

        assert(len(I) > 0)
        core_size = max(1, int(len(I) * core_ratio))
        random.shuffle(I)
        core = I[:core_size]
        remainder = I[core_size:]

        for i in core:
            num_uops = random.randrange(1, num_uops_per_insn + 1)
            for x in range(num_uops):
                sz = random.randrange(1, len(P)+1)
                p = list(random.sample(P, sz))
                res.assignment[i].append(p)

        for i in remainder:
            idx = random.randrange(0, len(core))
            core_element = core[idx]
            res.assignment[i] = res.assignment[core_element][:]
            # TODO this is not a full deep copy

        return res

    @classmethod
    def from_model(cls, arch: Architecture, model):
        """ Create a Mapping3 from a model, i.e. a tuple (i2u, u2p) of
            dictionaries.
            i2u maps pairs of instructions i from arch and some objects u
            representing uops to a True value iff i should be decomposed into u
            according to the mapping.
            u2p does the same for tuples of uop representations u and ports p to
            indicate that u can be executed on p.
        """
        (i2u, u2p) = model
        P = arch.port_list()
        res = cls(arch)
        for (i, u), v in i2u.items():
            uop = []
            for p in P:
                if u2p.get((u, p), False):
                    uop.append(p)
            if len(uop) > 0:
                res.assignment[i].append(uop)
        return res


class Mapping2(Mapping):
    """ Class representing port mappings where instructions are directly
        executed on ports.
    """
    def __init__(self, arch: Architecture):
        super().__init__()
        self.arch = arch

        # an assignment from instructions to lists of ports
        self.assignment = dict()

    def __getitem__(self, key):
        assert key in self.assignment
        return self.assignment[key]

    def __repr__(self):
        res = "Mapping2(arch={}, assignment={})".format(repr(self.arch), repr(self.assignment))
        return res

    def to_json_dict(self):
        res = dict()
        res["kind"] = "Mapping2"
        arch_dict = self.arch.to_json_dict()
        res_dict = dict()
        for k, v in arch_dict.items():
            res_dict[k] = jsonable.mark_noindent(v)
        res["arch"] = res_dict

        assignment_dict = dict()
        for i, ps in self.assignment.items():
            assignment_dict[i.name] = jsonable.mark_noindent([p.name for p in ps])
        res["assignment"] = assignment_dict

        return res

    def from_json_dict(self, jsondict):
        assert(jsondict["kind"] == "Mapping2")
        arch = self.arch
        assignment_dict = jsondict["assignment"]
        for i, ps in assignment_dict.items():
            insn = arch.insns[i]
            self.assignment[insn] = sorted([arch.ports[p] for p in ps])

    @classmethod
    def from_random(cls, arch: Architecture):
        """ Generate a new random Mapping for the given architecture.
        """
        return cls.from_random_with_core(arch, 1.0)

    @classmethod
    def from_random_with_core(cls, arch: Architecture, core_ratio):
        """ Generate a new random Mapping for the given architecture.
            Only core_ratio * number of instructions many instructions are
            generated randomly, the others are composed of core instructions.
        """
        assert(0.0 <= core_ratio and core_ratio <= 1.0)

        res = cls(arch)

        I = arch.insn_list()
        P = arch.port_list()

        assert(len(I) > 0)
        core_size = max(1, int(len(I) * core_ratio))
        random.shuffle(I)
        core = I[:core_size]
        remainder = I[core_size:]

        for i in core:
            sz = random.randrange(1, len(P)+1)
            p = list(random.sample(P, sz))
            res.assignment[i] = p

        for i in remainder:
            idx = random.randrange(0, len(core))
            core_element = core[idx]
            res.assignment[i] = res.assignment[core_element][:]

        return res

    @classmethod
    def from_model(cls, arch: Architecture, model):
        """ Create a Mapping2 from a model, i.e. a dictionary i2p.
            i2p maps pairs of instructions i from arch and ports to a True value
            iff i can be executed on p according to the mapping.
        """
        i2p = model
        I = arch.insn_list()
        P = arch.port_list()
        res = cls(arch)

        for i in I:
            res.assignment[i] = []

        for (i, p), v in i2p.items():
            if v:
                res.assignment[i].append(p)
        return res
