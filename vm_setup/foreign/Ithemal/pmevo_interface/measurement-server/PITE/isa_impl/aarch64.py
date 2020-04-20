# vim: et:ts=4:sw=4:fenc=utf-8

import PITE.isa as isa
import PITE.register_file as reg

class AArch64_ISA(isa.ISA):
    name = "aarch64"
    dirname = "aarch64"
    immediate_prefix = ''

    def __init__(self, settings):
        super().__init__(settings)
        self.register_file = reg.AArch64_RegisterFile()
        self.program_frame = self.program_frame.replace("{INCLUDES}", self.includes, 1)
        self.program_frame = self.program_frame.replace("{ASM_INIT}", self.asm_init, 1)
        self.program_frame = self.program_frame.replace("{ASM_INSTRUCTIONS}", self.asm_loop, 1)
        self.program_frame = self.program_frame.replace("{WARMUP_CODE}", self.warmup_code,1)

    def init_code_for_register(self, reg):
        if reg.startswith("x"):
            return '"    mov {reg}, #42\\n"\n'.format(reg=reg)
        if reg.startswith("v"):
            return '"    fmov {reg}.4s, 24.0\\n"\n'.format(reg=reg)
        assert False

    includes = ""

    # code that is executed before time measurement starts
    asm_init = """\
    __asm__ __volatile__ (
        "   mrs x0, FPCR \\n" // Read Floating-point Control Register
        "   orr x0, x0, 0x1000000 \\n" // set bit 24, enable flush-to-zero mode for denormal floats
        "   msr FPCR, x0 \\n" // Write Floating-point Control Register
        : /* no output */
        : /* no input */
        : "x0"
    );"""

    asm_loop =  """\
    __asm__ __volatile__ (
{init_code}
        "   mov w0, #0 \\n"
        "   mov w1, #{lower16bit} \\n"
        "   movk w1, #{upper16bit}, LSL #16 \\n"
        "   b .TestbenchLabel1 \\n"
        "   .p2align 4,,15\\n"
        ".TestbenchLabel2: \\n"
{loop_body}
        "   add w0, w0, #1 \\n"
        ".TestbenchLabel1: \\n"
        "   cmp w0, w1 \\n"
        "   blt .TestbenchLabel2 \\n"
        : /* no output */
        : "r" (mem), /* input for memory operands */
          "r" (div)  /* input for divisor operands */
        : "x0", "x1" {used_regs}
    );"""

    # warmup_code = asm_loop.replace("{lower16bit}", "0").replace("{upper16bit}", "1000").replace("TestbenchLabel", "WarmupLabel")
    warmup_code = ""

def get_isas():
    return [AArch64_ISA]

