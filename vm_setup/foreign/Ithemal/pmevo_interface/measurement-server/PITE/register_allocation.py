# vim: et:ts=4:sw=4:fenc=utf-8

from collections import defaultdict
import re

import PITE.isa

class Allocator:
    """
        Tool for allocating operands for lists of instruction instances.
        It tries to maximize the distance between the definition and the use of
        values such that hopefully all dependencies are readily computed when
        an instruction instance is executed.
    """
    step_mem_offset = 64
    # step_mem_offset = 256
    max_mem_offset = 4032
    # max_mem_offset = 4096
    # max_mem_offset = 8192
    # max_mem_offset = 16384
    # max_mem_offset = 2048

    def __init__(self, isa):
        self.isa = isa
        self.regfile = isa.get_register_file()
        self.next_mem_offset = self.step_mem_offset

        # maps register category to the index of the next register to use for writing
        self.write_indices = defaultdict(lambda:0)

        # maps register category to an index one ahead of the next register to use for reading
        self.read_indices = defaultdict(lambda:0)

    def get_mem_offset(self):
        """
            Obtain a number to be used as a memory offset. Consecutive calls
            generate numbers that are far enough from each other to avoid
            depedencies among successive memory accesses.
        """
        res = self.next_mem_offset
        if self.next_mem_offset >= self.max_mem_offset:
            self.next_mem_offset = self.step_mem_offset
        else:
            self.next_mem_offset += self.step_mem_offset
        return res

    def get_register(self, cat, width, write):
        """
            Obtain next register and update index to point to the next
            register. The last argument decides whether the index for writing
            or reading operands is used.
        """
        if write:
            indices = self.write_indices
        else:
            indices = self.read_indices
        res_cat = self.regfile.registers[cat]
        res_group = res_cat[indices[cat]]
        indices[cat] += 1
        indices[cat] %= len(res_cat)
        res = res_group[width]
        return res

    def reset_read_registers(self):
        """
            Reset all read indices such that the next register to use for
            reading is the one after the next register to write.
        """
        for cat in self.regfile.registers.keys():
            self.read_indices[cat] = self.write_indices[cat]

    def allocate_registers(self, iseq):
        for insn in iseq:
            writing_placeholders = ( ph for ph in insn.placeholders if ph.is_writing )
            other_placeholders = ( ph for ph in insn.placeholders if not ph.is_writing )

            # first assign registers to writing operands so that  we don't use
            # these for reading
            for placeholder in writing_placeholders:
                assert placeholder.is_register
                replacement = self.get_register(placeholder.reg_category, placeholder.width, write=True)
                placeholder.assign(replacement)

            self.reset_read_registers()

            # assign registers to all other operands
            for placeholder in other_placeholders:
                replacement = None
                if placeholder.is_immediate:
                    imm = 44
                    replacement = self.isa.as_imm(imm)
                elif placeholder.is_mem_offset:
                    replacement = str(self.get_mem_offset())
                elif placeholder.is_mem:
                    replacement = self.regfile.registers["MEM"][0][placeholder.width]
                elif placeholder.is_div:
                    replacement = self.regfile.registers["DIV"][0][placeholder.width]
                elif placeholder.is_register:
                    assert not placeholder.is_writing
                    replacement = self.get_register(placeholder.reg_category, placeholder.width, write=False)
                assert replacement is not None, "Invalid placeholder: {}".format(placeholder)
                placeholder.assign(replacement)

