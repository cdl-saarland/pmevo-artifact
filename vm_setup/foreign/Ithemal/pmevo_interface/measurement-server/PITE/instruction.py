# vim: et:ts=4:sw=4:fenc=utf-8

import copy
import math
import re

class InstructionForm:
    """
        Representation of the abstract concept of an instruction, containing
        information about the operands that it requires.
        Use get_instance() to obtain an instance of this instruction.
    """
    def __init__(self, text):
        # TODO
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text

    def get_instance(self):
        return InstructionInstance(insnform=self)

class InstructionInstance:
    """
        An instantiation of an instruction form with placeholders that can be
        mapped to actual operands.
    """
    placeholder_delim = "((", "))"
    pattern = re.escape(placeholder_delim[0]) + "((?:\w|:)+)" + re.escape(placeholder_delim[1])

    def __init__(self, insnform):
        self.insnform = insnform
        self.operands = dict()
        ms = re.findall(self.pattern, self.insnform.text)
        self.placeholders = [ Placeholder(insn=self, idx=idx, text=m) for idx, m in enumerate(ms) ]

    def __str__(self):
        return self.get_str()

    def __repr__(self):
        return self.get_str()

    def get_str(self):
        res = self.insnform.text
        for ph in self.placeholders:
            res = re.sub(self.pattern, self.operands[ph.idx], res, count=1)
        return res

    def get_code(self):
        str_rep = self.get_str()
        res = " " * 8 + '"{}\\n"'.format(str_rep)
        return res

class Placeholder:
    """
        Representation of an operand placeholder in an instruction instance.
        The properties of the placeholder are parsed from its string
        representation.
        options:
            IMM:<width>
            MIMM:<width>
            MEM:<width>
            DIV:<width>
            REG:W:<kind>:<width>
            REG:R:<kind>:<width>
            REG:RW:<kind>:<width>
    """
    def __init__(self, insn, idx, text):
        self.placeholder = text
        self.insn = insn
        self.idx = idx

        self.is_mem = False
        self.is_div = False
        self.is_register = False
        self.is_mem_offset = False
        self.is_immediate = False

        self.is_writing = False
        self.is_reading = False

        self.reg_category = None
        self.width = None

        elems = text.split(":")

        assert len(elems) > 0
        if elems[0] == "IMM":
            assert len(elems) == 2
            self.is_immediate = True
        elif elems[0] == "MIMM":
            assert len(elems) == 2
            self.is_mem_offset = True
        elif elems[0] == "MEM":
            assert len(elems) == 2
            self.is_mem = True
        elif elems[0] == "DIV":
            assert len(elems) == 2
            self.is_div = True
        elif elems[0] == "REG":
            assert len(elems) == 4
            assert len(elems[1]) <= 2
            self.is_register = True
            self.is_writing = "W" in elems[1]
            self.is_reading = "R" in elems[1]
            self.reg_category = elems[2]
        else:
            assert False, "Invalid placeholder: {}".format(text)

        self.width = elems[-1]

    def assign(self, text):
        self.insn.operands[self.idx] = text

    def __str__(self):
        return self.placeholder

    def __repr__(self):
        return self.placeholder

