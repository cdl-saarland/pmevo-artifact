#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod

from collections import defaultdict
import re


class RegisterFile(ABC):
    registers = NotImplemented

    def __init__(self):
        # for each register kind an index pointing to the next register to use
        self.reset_indices()

    def reset_indices(self):
        self.next_indices = defaultdict(lambda:0)

    def get_memory_base(self):
        return self.registers["MEM"][0]["64"]

    def get_div_register(self):
        return self.registers["DIV"][0]["64"]

    def get_clobber_list(self):
        res = []
        for k, v in self.registers.items():
            for regset in v:
                reg = regset["repr"]
                if reg is not None:
                    res.append(reg)
        return res



class X86_64_RegisterFile(RegisterFile):
    registers = {
        "G": # general purpose registers
            [
                # {"64": "rax", "32": "eax", "repr": "rax"},
                # {"64": "rcx", "32": "ecx", "repr": "rcx"},
                # {"64": "rdx", "32": "edx", "repr": "rdx"},
                {"64": "rbx", "32": "ebx", "repr": "rbx"}, # used by gcc
                # {"64": "rsp", "32": "esp", "repr": "rsp"}, # used by gcc
                # {"64": "rbp", "32": "ebp", "repr": "rbp"}, # used by gcc
                {"64": "rsi", "32": "esi", "repr": "rsi"}, # used for string instructions
                {"64": "rdi", "32": "edi", "repr": "rdi"}, # used for string instructions
                {"64": "r8", "32": "r8d", "repr": "r8"},
                {"64": "r9", "32": "r9d", "repr": "r9"},
                {"64": "r10", "32": "r10d", "repr": "r10"},
                {"64": "r11", "32": "r11d", "repr": "r11"},
                {"64": "r12", "32": "r12d", "repr": "r12"},
                # {"64": "r13", "32": "r13d", "repr": "r13"}, # used as divisor register
                # {"64": "r14", "32": "r14d", "repr": "r14"}, # used as memory register
                # {"64": "r15", "32": "r15d", "repr": "r15"}, # used by program frame
            ],
        "V": # vector registers
            [
                {"256": "ymm0", "128": "xmm0", "repr": "ymm0"},
                {"256": "ymm1", "128": "xmm1", "repr": "ymm1"},
                {"256": "ymm2", "128": "xmm2", "repr": "ymm2"},
                {"256": "ymm3", "128": "xmm3", "repr": "ymm3"},
                {"256": "ymm4", "128": "xmm4", "repr": "ymm4"},
                {"256": "ymm5", "128": "xmm5", "repr": "ymm5"},
                {"256": "ymm6", "128": "xmm6", "repr": "ymm6"},
                {"256": "ymm7", "128": "xmm7", "repr": "ymm7"},
                {"256": "ymm8", "128": "xmm8", "repr": "ymm8"},
                {"256": "ymm9", "128": "xmm9", "repr": "ymm9"},
                {"256": "ymm10", "128": "xmm10", "repr": "ymm10"},
                {"256": "ymm11", "128": "xmm11", "repr": "ymm11"},
                {"256": "ymm12", "128": "xmm12", "repr": "ymm12"},
                {"256": "ymm13", "128": "xmm13", "repr": "ymm13"},
                {"256": "ymm14", "128": "xmm14", "repr": "ymm14"},
                {"256": "ymm15", "128": "xmm15", "repr": "ymm15"},
            ],
        "DIV": # register for non-zero divisor
            [
                {"64": "r13", "32": "r13d", "repr": None},
                # no need to represent this in the clobber list as it is
                # hardwired to a this register anyway
            ],
        "MEM": # base register for memory operands
            [
                {"64": "r14", "32": "r14d", "repr": None}
                # no need to represent this in the clobber list as it is
                # hardwired to a this register anyway
            ],
        }

    def __init__(self):
        super().__init__()



class AArch64_RegisterFile(RegisterFile):
    registers = {
        "G": # general puprose registers
            [
                # {"64": "x0", "32": "w0", "repr": "x0"}, # used for frame
                # {"64": "x1", "32": "w1", "repr": "x1"}, # used for frame
                {"64": "x2", "32": "w2", "repr": "x2"},
                {"64": "x3", "32": "w3", "repr": "x3"},
                {"64": "x4", "32": "w4", "repr": "x4"},
                {"64": "x5", "32": "w5", "repr": "x5"},
                {"64": "x6", "32": "w6", "repr": "x6"},
                {"64": "x7", "32": "w7", "repr": "x7"},
                {"64": "x8", "32": "w8", "repr": "x8"},
                {"64": "x9", "32": "w9", "repr": "x9"},
                {"64": "x10", "32": "w10", "repr": "x10"},
                {"64": "x11", "32": "w11", "repr": "x11"},
                {"64": "x12", "32": "w12", "repr": "x12"},
                {"64": "x13", "32": "w13", "repr": "x13"},
                {"64": "x14", "32": "w14", "repr": "x14"},
                {"64": "x15", "32": "w15", "repr": "x15"},
                {"64": "x16", "32": "w16", "repr": "x16"},
                {"64": "x17", "32": "w17", "repr": "x17"},
                {"64": "x18", "32": "w18", "repr": "x18"},
                {"64": "x19", "32": "w19", "repr": "x19"},
                {"64": "x20", "32": "w20", "repr": "x20"},
                {"64": "x21", "32": "w21", "repr": "x21"},
                {"64": "x22", "32": "w22", "repr": "x22"},
                {"64": "x23", "32": "w23", "repr": "x23"},
                {"64": "x24", "32": "w24", "repr": "x24"},
                {"64": "x25", "32": "w25", "repr": "x25"},
                {"64": "x26", "32": "w26", "repr": "x26"},
                {"64": "x27", "32": "w27", "repr": "x27"},
                # {"64": "x28", "32": "w28", "repr": "x28"}, # used for memory
                # {"64": "x29", "32": "w29", "repr": "x29"}, # used for divisor
                # {"64": "x30", "32": "w30", "repr": "x30"}, # link register
                # {"64": "x31", "32": "w31", "repr": "x31"}, # zero/sp register
            ],
        "F": # vector/floating point registers
            [
                {"VEC": "v0", "128": "q0", "64": "d0", "32": "s0", "16": "h0", "8": "b0", "repr": "v0"},
                {"VEC": "v1", "128": "q1", "64": "d1", "32": "s1", "16": "h1", "8": "b1", "repr": "v1"},
                {"VEC": "v2", "128": "q2", "64": "d2", "32": "s2", "16": "h2", "8": "b2", "repr": "v2"},
                {"VEC": "v3", "128": "q3", "64": "d3", "32": "s3", "16": "h3", "8": "b3", "repr": "v3"},
                {"VEC": "v4", "128": "q4", "64": "d4", "32": "s4", "16": "h4", "8": "b4", "repr": "v4"},
                {"VEC": "v5", "128": "q5", "64": "d5", "32": "s5", "16": "h5", "8": "b5", "repr": "v5"},
                {"VEC": "v6", "128": "q6", "64": "d6", "32": "s6", "16": "h6", "8": "b6", "repr": "v6"},
                {"VEC": "v7", "128": "q7", "64": "d7", "32": "s7", "16": "h7", "8": "b7", "repr": "v7"},
                {"VEC": "v8", "128": "q8", "64": "d8", "32": "s8", "16": "h8", "8": "b8", "repr": "v8"},
                {"VEC": "v9", "128": "q9", "64": "d9", "32": "s9", "16": "h9", "8": "b9", "repr": "v9"},
                {"VEC": "v10", "128": "q10", "64": "d10", "32": "s10", "16": "h10", "8": "b10", "repr": "v10"},
                {"VEC": "v11", "128": "q11", "64": "d11", "32": "s11", "16": "h11", "8": "b11", "repr": "v11"},
                {"VEC": "v12", "128": "q12", "64": "d12", "32": "s12", "16": "h12", "8": "b12", "repr": "v12"},
                {"VEC": "v13", "128": "q13", "64": "d13", "32": "s13", "16": "h13", "8": "b13", "repr": "v13"},
                {"VEC": "v14", "128": "q14", "64": "d14", "32": "s14", "16": "h14", "8": "b14", "repr": "v14"},
                {"VEC": "v15", "128": "q15", "64": "d15", "32": "s15", "16": "h15", "8": "b15", "repr": "v15"},
                {"VEC": "v16", "128": "q16", "64": "d16", "32": "s16", "16": "h16", "8": "b16", "repr": "v16"},
                {"VEC": "v17", "128": "q17", "64": "d17", "32": "s17", "16": "h17", "8": "b17", "repr": "v17"},
                {"VEC": "v18", "128": "q18", "64": "d18", "32": "s18", "16": "h18", "8": "b18", "repr": "v18"},
                {"VEC": "v19", "128": "q19", "64": "d19", "32": "s19", "16": "h19", "8": "b19", "repr": "v19"},
                {"VEC": "v20", "128": "q20", "64": "d20", "32": "s20", "16": "h20", "8": "b20", "repr": "v20"},
                {"VEC": "v21", "128": "q21", "64": "d21", "32": "s21", "16": "h21", "8": "b21", "repr": "v21"},
                {"VEC": "v22", "128": "q22", "64": "d22", "32": "s22", "16": "h22", "8": "b22", "repr": "v22"},
                {"VEC": "v23", "128": "q23", "64": "d23", "32": "s23", "16": "h23", "8": "b23", "repr": "v23"},
                {"VEC": "v24", "128": "q24", "64": "d24", "32": "s24", "16": "h24", "8": "b24", "repr": "v24"},
                {"VEC": "v25", "128": "q25", "64": "d25", "32": "s25", "16": "h25", "8": "b25", "repr": "v25"},
                {"VEC": "v26", "128": "q26", "64": "d26", "32": "s26", "16": "h26", "8": "b26", "repr": "v26"},
                {"VEC": "v27", "128": "q27", "64": "d27", "32": "s27", "16": "h27", "8": "b27", "repr": "v27"},
                {"VEC": "v28", "128": "q28", "64": "d28", "32": "s28", "16": "h28", "8": "b28", "repr": "v28"},
                {"VEC": "v29", "128": "q29", "64": "d29", "32": "s29", "16": "h29", "8": "b29", "repr": "v29"},
                {"VEC": "v30", "128": "q30", "64": "d30", "32": "s30", "16": "h30", "8": "b30", "repr": "v30"},
                {"VEC": "v31", "128": "q31", "64": "d31", "32": "s31", "16": "h31", "8": "b31", "repr": "v31"},
            ],
        "DIV": # register for non-zero divisor
            [
                {"64": "x29", "32": "w29", "repr": None},
                # no need to represent this in the clobber list as it is
                # hardwired to a this register anyway
            ],
        "MEM": # base register for memory operands
            [
                {"64": "x28", "32": "w28", "repr": None},
                # no need to represent this in the clobber list as it is
                # hardwired to a this register anyway
            ],
        }

    def __init__(self):
        super().__init__()

