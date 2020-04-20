# vim: et:ts=4:sw=4:fenc=utf-8


import PITE.isa as isa
import PITE.register_file as reg


class X86_64_ISA(isa.ISA):
    name = "x86_64"
    dirname = "x86_64"
    immediate_prefix = ''

    init_val = 42

    def __init__(self, settings):
        super().__init__(settings)
        self.register_file = reg.X86_64_RegisterFile()
        self.program_frame = self.program_frame.replace("{INCLUDES}", self.includes, 1)
        self.program_frame = self.program_frame.replace("{ASM_INIT}", self.asm_init, 1)
        self.program_frame = self.program_frame.replace("{ASM_INSTRUCTIONS}", self.asm_loop, 1)
        self.program_frame = self.program_frame.replace("{WARMUP_CODE}", self.warmup_code, 1)

    def init_code_for_register(self, reg):
        if reg.startswith("r"):
            return '        "   mov {reg}, {val}\\n"\n'.format(reg=reg, val=self.init_val)
        if reg.startswith("ymm"):
            xmm_reg = reg.replace("y", "x", 1)
            return """
        "   mov r15d, {val}\\n"
        "   vcvtsi2ss {xreg}, {xreg}, r15d\\n"
        "   vpermilps {xreg}, {xreg}, 0\\n"
        "   vinsertf128 {reg}, {reg}, {xreg}, 1\\n"\
""".format(reg=reg, xreg=xmm_reg, val=self.init_val)
        assert False

    includes = "#include <xmmintrin.h>"

    # code that is executed before time measurement starts
    asm_init = "    _mm_setcsr( _mm_getcsr() | (1<<15) | (1<<6)); // disable denormal floats"

        # "   mov rdi, {membasereg}\\n" // initialize traditional string address registers
        # "   mov rsi, {membasereg}\\n" // initialize traditional string address registers
    asm_loop = """\
    __asm__ __volatile__ (
        "   .intel_syntax noprefix\\n"
{init_code}
        "   mov r15, {num_iterations}\\n"
        "   mov rcx, 4\\n"  // prepare shift amount
        "   .p2align 4,,15\\n"
        "TestbenchLabel:\\n"
        // benchmarked instructions begin
{loop_body}
        // benchmarked instructions end
        "   sub r15, 1\\n"
        "   jnz TestbenchLabel\\n"
        "   .att_syntax\\n"
        : /* no output */
        : "r" (mem), /* input for memory operands */
          "r" (div)  /* input for divisor operands */
        : "r15", "rcx", "rax", "rdx" {used_regs}
    );"""

    warmup_code = asm_loop.replace("{num_iterations}", "1000").replace("TestbenchLabel", "WarmupLabel")

def get_isas():
    return [X86_64_ISA]

