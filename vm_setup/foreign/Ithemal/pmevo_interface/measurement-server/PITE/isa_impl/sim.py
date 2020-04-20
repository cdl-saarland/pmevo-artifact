# vim: et:ts=4:sw=4:fenc=utf-8

import os
import re
import subprocess

import PITE.isa as isa
import PITE.register_file as reg

class SimISA(isa.ISA):
    name = NotImplemented
    dirname = NotImplemented
    immediate_prefix = ''

    def is_simulated(self):
        return True

    def __init__(self, settings):
        super().__init__(settings)
        self.register_file = NotImplemented
        self.program_frame = NotImplemented

    def init_code_for_register(self, reg):
        return ""

x86_64_sim_frame = """
void *aligned_alloc(long unsigned int alignment, long unsigned int size);

int kernel(int n) {{
    void * memt = aligned_alloc(4096, 4096);
    register void * mem asm("{membasereg}") = memt;
    register long long div asm("{div_reg}") = 44; // initialize the non-zero divisor register
    __asm__ __volatile__ (
        "movl $111, %%ebx\\n" // IACA start marker
        ".byte 0x64, 0x67, 0x90\\n"
        "   .intel_syntax noprefix\\n"
        "# LLVM-MCA-BEGIN\\n"
{loop_body}
        "# LLVM-MCA-END\\n"
        "   .att_syntax\\n"
        "movl $222, %%ebx\\n" // IACA end marker
        ".byte 0x64, 0x67, 0x90\\n"
    : /* no output */
    : "r" (mem), /* input for memory operands */
      "r" (div)  /* input for divisor operands */
    : "ebx", "rax", "rdx" {used_regs}, "memory"
    );
    return 0;
}}
"""

class IACA_intel_ISA(SimISA):
    name = "IACAx86_64"
    dirname = "x86_64"
    immediate_prefix = ''
    additional_cc_flags = ["-c"]

    def __init__(self,settings):
        super().__init__(settings)
        self.register_file = reg.X86_64_RegisterFile()
        self.parsing_re = re.compile(r"Block Throughput: (\d+\.\d+)")
        self.program_frame = x86_64_sim_frame

    def create_command(self, bmk_bin):
        command = []
        command.append(os.path.join(self.settings.iaca_path, "iaca"))
        command.append(bmk_bin)
        return command

    def extract_result(self, str_res, num_testcase_instances):
        m = self.parsing_re.search(str_res)
        if m is None:
            return { 'cycles': None, 'error_cause': "throughput missing in iaca output" }

        total_cycles = float(m.group(1))
        cycles = total_cycles / num_testcase_instances
        return {'cycles': cycles}

class Ithemal_intel_ISA(SimISA):
    name = "Ithemalx86_64"
    dirname = "x86_64"
    immediate_prefix = ''
    additional_cc_flags = ["-c"]

    def __init__(self,settings):
        super().__init__(settings)
        self.register_file = reg.X86_64_RegisterFile()
        self.parsing_re = re.compile(r"(\d+\.\d+)")
        self.program_frame = x86_64_sim_frame

    def create_command(self, bmk_bin):
        command = []
        command += ["/home/ithemal/ithemal/learning/pytorch/ithemal/predict.py"]
        command += ["--model", "/home/ithemal/ithemal/skylake/predictor.dump"]
        command += ["--model-data", "/home/ithemal/ithemal/skylake/trained.mdl"]
        command += ["--file", bmk_bin]
        return command

    def extract_result(self, str_res, num_testcase_instances):
        m = self.parsing_re.search(str_res)
        if m is None:
            return { 'cycles': None, 'error_cause': "throughput missing in ithemal output" }

        total_cycles = float(m.group(1))
        total_cycles = total_cycles / 100.0
        cycles = total_cycles / num_testcase_instances
        return {'cycles': cycles}

class LLVMMCA_ISA(SimISA):
    additional_cc_flags = ["-c", "-S"]
    def __init__(self,settings):
        super().__init__(settings)
        self.parsing_re = re.compile(r"Total Cycles:\s*(\d+)")

    def create_command(self, bmk_bin):
        command = []
        command.append(os.path.join(self.settings.llvm_mca_path, "llvm-mca"))
        command.extend(self.mca_args)
        command.append(bmk_bin)
        return command

    def extract_result(self, str_res, num_testcase_instances):
        m = self.parsing_re.search(str_res)
        if m is None:
            return { 'cycles': None, 'error_cause': "throughput missing in llvm-mca output" }

        total_cycles = float(m.group(1))
        total_cycles = total_cycles / 100.0
        cycles = total_cycles / num_testcase_instances
        return {'cycles': cycles}

class LLVMMCA_skylake_ISA(LLVMMCA_ISA):
    name = "LLVMMCA_SKLx86_64"
    dirname = "x86_64"
    immediate_prefix = ''
    additional_cc_flags = ["-c", "-S", "--target=x86_64"]
    mca_args = ["-march=x86-64", "-mcpu=skylake"]

    def __init__(self,settings):
        super().__init__(settings)
        self.register_file = reg.X86_64_RegisterFile()
        self.program_frame = x86_64_sim_frame

class LLVMMCA_ZENP_ISA(LLVMMCA_ISA):
    name = "LLVMMCA_ZENPx86_64"
    dirname = "x86_64"
    immediate_prefix = ''
    additional_cc_flags = ["-c", "-S", "--target=x86_64"]
    mca_args = ["-march=x86-64", "-mcpu=znver1"]

    def __init__(self,settings):
        super().__init__(settings)
        self.register_file = reg.X86_64_RegisterFile()
        self.program_frame = x86_64_sim_frame


aarch64_sim_frame = """
void *aligned_alloc(long unsigned int alignment, long unsigned int size);

int kernel(int n) {{
    void * memt = aligned_alloc(4096, 4096);
    register void * mem asm("{membasereg}") = memt;
    register long long div asm("{div_reg}") = 44; // initialize the non-zero divisor register
    __asm__ __volatile__ (
        "# LLVM-MCA-BEGIN\\n"
{loop_body}
        "# LLVM-MCA-END\\n"
    : /* no output */
    : "r" (mem), /* input for memory operands */
      "r" (div)  /* input for divisor operands */
    : "x0" {used_regs}, "memory"
    );
    return 0;
}}
"""

class LLVMMCA_A72_ISA(LLVMMCA_ISA):
    name = "LLVMMCA_A72_ARM"
    dirname = "aarch64"
    immediate_prefix = ''
    additional_cc_flags = ["-c", "-S", "--target=aarch64"]
    mca_args = ["-march=aarch64", "-mcpu=cortex-a72"]

    def __init__(self,settings):
        super().__init__(settings)
        self.register_file = reg.AArch64_RegisterFile()
        self.program_frame = aarch64_sim_frame

    def create_command(self, bmk_bin):
        rv = subprocess.run(["sed", "s|// LLVM|# LLVM|", "-i", bmk_bin])
        command = []
        command.append(os.path.join(self.settings.llvm_mca_path, "llvm-mca"))
        command.extend(self.mca_args)
        command.append(bmk_bin)
        return command

def get_isas():
    return [IACA_intel_ISA, Ithemal_intel_ISA, LLVMMCA_skylake_ISA, LLVMMCA_ZENP_ISA, LLVMMCA_A72_ISA]

