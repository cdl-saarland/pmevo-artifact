# vim: et:ts=4:sw=4:fenc=utf-8

from typing import *

from utils.jsonable import JSONable

def normalize_insn(name):
    name = name.replace(" ", "_")
    name = name.replace("\t", "_")
    return name


class Insn:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return "I_{" + self.name + "}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        return False

    def __lt__(self, other):
        if type(other) is type(self):
            return self.name < other.name
        return False

    def __hash__(self):
        return hash(self.name)

class Port:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return "P_{" + self.name + "}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        return False

    def __lt__(self, other):
        if type(other) is type(self):
            return self.name < other.name
        return False

    def __hash__(self):
        return hash(self.name)

class Architecture(JSONable):
    def __init__(self):
        super().__init__()
        self.insns = dict()
        self.ports = dict()
        self.name = None
        self.restricted = None

    def insn_list(self):
        if  self.restricted is not None:
            insns = filter(lambda x: x in self.restricted, self.insns.values())
        else:
            insns = self.insns.values()
        return sorted(insns)

    def port_list(self):
        return sorted(self.ports.values())

    def add_insn(self, name: str):
        normalized_name = normalize_insn(name)
        assert(name not in self.insns.keys())
        new_insn = Insn(normalized_name)
        self.insns[normalized_name] = new_insn
        return new_insn

    def add_port(self, name: str):
        assert(name not in self.ports.keys())
        new_port = Port(name)
        self.ports[name] = new_port
        return new_port

    def add_insns(self, names: List[str]):
        for n in names:
            self.add_insn(n)

    def add_ports(self, names: List[str]):
        for n in names:
            self.add_port(n)

    def add_number_of_ports(self, num: int):
        self.add_ports([str(i) for i in range(0, num)])

    def restrict_insns(self, insns):
        self.restricted = list(insns)

    def unrestrict_insns(self):
        self.restricted = None

    def __repr__(self):
        res = "Architecture(insns={}, ports={})".format(repr(self.insns), repr(self.ports))
        return res

    def verify_json_dict(self, jsondict):
        # check whether new architecture is identical to the current one
        curr_insns = set(map(lambda x: x.name, self.insn_list()))
        new_insns = set(jsondict["insns"])
        if curr_insns != new_insns:
            print("curr_insns:")
            print(curr_insns)
            print("new_insns:")
            print(new_insns)
        assert(curr_insns == new_insns)

        curr_ports = set(map(lambda x: x.name, self.port_list()))
        new_ports = set(jsondict["ports"])
        if curr_ports != new_ports:
            print("curr_ports:")
            print(curr_ports)
            print("new_ports:")
            print(new_ports)
        assert(curr_ports == new_ports)

        other_name = jsondict.get("name", None)
        if self.name is not None and other_name is not None:
            assert(self.name == other_name)
        return

    def from_json_dict(self, jsondict):
        if jsondict["kind"] != "Architecture" and "arch" in jsondict:
            # enable reading architectures from mapping jsons, etc.
            jsondict = jsondict["arch"]

        assert(jsondict["kind"] == "Architecture")

        input_insn_list = jsondict["insns"]
        for s in input_insn_list:
            if s not in self.insns:
                self.add_insn(s)

        input_port_list = jsondict["ports"]
        for s in input_port_list:
            if s not in self.ports:
                self.add_port(s)

        self.name = jsondict.get("name", None)


    def to_json_dict(self):
        res = dict()
        res["kind"] = "Architecture"
        res["insns"] = [ i.name for i in self.insn_list() ]
        res["ports"] = [ p.name for p in self.port_list() ]
        if self.name is not None:
            res["name"] = self.name
        return res

