# vim: et:ts=4:sw=4:fenc=utf-8


class Port:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "P_{" + self.name + "}"

    def __repr__(self):
        return self.__str__()

    def get_name(self):
        return self.name

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)


class Uop:
    def __init__(self, insn, idx: int):
        self.insn = insn
        self.idx = idx

    @property
    def name(self):
        return str(self.idx)

    def __str__(self):
        if self.insn is None:
            return "U_{" + str(self.idx) + "}"
        else:
            return "U_{" + str(self.insn) + "," + str(self.idx) + "}"

    def __repr__(self):
        return self.__str__()

    def get_insn(self):
        return self.insn

    def get_idx(self):
        return self.idx

    def __eq__(self, other):
        if type(other) is type(self):
            return self.insn == other.insn and self.idx == other.idx
        return False

    def __hash__(self):
        if self.insn is None:
            return hash(self.idx)
        else:
            return hash(self.insn) + hash(self.idx)


class Insn:
    def __init__(self, name, num_uops=0):
        self.name = name
        self.possible_uops = []
        for x in range(num_uops):
            self.possible_uops.append(Uop(self, x))

    def add_uop(self):
        idx = len(self.possible_uops)
        new_uop = Uop(self, idx)
        self.possible_uops.append(new_uop)
        return new_uop

    def __str__(self):
        return "I_{" + self.name + "}"

    def __repr__(self):
        return self.__str__()

    def get_name(self):
        return self.name

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

    def get_uops(self):
        return self.possible_uops
