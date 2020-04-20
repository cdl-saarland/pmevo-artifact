# vim: et:ts=4:sw=4:fenc=utf-8

import PITE.instruction as instruction

import sys
import os
import subprocess
import re
import json
import importlib

from abc import ABC, abstractmethod
from shutil import which

def create_ISA(settings, isa_name=None):
    if isa_name is None:
        isa_name = subprocess.run(
            ["uname", "-m"],
            stdout=subprocess.PIPE,
        ).stdout.decode(
            "utf-8",
        )
        isa_name = isa_name.strip()
        print("Identified ISA: '{}'".format(isa_name))
    assert isa_name is not None
    settings.isa = isa_name

    available_ISAs = []

    # Look for available ISAs in isa_impl folder. Files there have to implement
    # the get_isas() function.
    path = os.path.dirname(os.path.abspath(globals()["__file__"]))
    (_, _, filenames) = next(os.walk(os.path.join(path, "isa_impl")))
    for fn in filenames:
        if not fn.endswith(".py"):
            continue
        module_name = "PITE.isa_impl.{}".format(fn[:-len(".py")])
        m = importlib.import_module(module_name)
        available_ISAs += m.get_isas()

    for ISA_cls in available_ISAs:
        if isa_name == ISA_cls.name:
            return ISA_cls(settings)
    raise RuntimeError("Unsupported ISA!")


def parse_instructionlist(filename):
    instruction_list = []
    with open(filename, "r") as f_insnlist:
        lines = f_insnlist.readlines()
        for line in lines:
            line = line[:-1]
            instruction_list.append(instruction.InstructionForm(str(line)))
    return instruction_list

class ISA(ABC):
    additional_cc_flags = None

    def __init__(self, settings):
        self.settings = settings
        self.__get_description__()

    def is_simulated(self):
        return False

    def get_register_file(self):
        return self.register_file

    def get_program_frame(self):
        return self.program_frame

    def get_immediate_prefix(self):
        return self.immediate_prefix

    def as_imm(self, imm):
        return "{prefix}{imm}".format(prefix=self.get_immediate_prefix(), imm=imm)

    def compile_and_run(self, iseq, cpufreq, num_iterations, num_testcase_instances, freq_path):
        bmk_src = self.settings.benchmark_src
        bmk_bin = self.settings.benchmark_bin

        # write code to src file
        assert num_iterations < 2**32
        hex_mask = 0xFFFF
        upper_N = (num_iterations >> 16) & hex_mask
        lower_N = num_iterations & hex_mask

        used_registers = ""
        init_code = ""
        for reg in self.register_file.get_clobber_list():
            used_registers += ', "' + reg + '"'
            init_code += self.init_code_for_register(reg)

        loop_body = "\n".join([ i.get_code() for i in iseq ])

        program = self.program_frame.format(
                num_iterations = num_iterations,
                frequency = cpufreq,
                num_instances_per_iteration = num_testcase_instances,
                loop_body = loop_body,
                init_code = init_code,
                lower16bit = lower_N,
                upper16bit = upper_N,
                used_regs = used_registers,
                membasereg = self.get_register_file().get_memory_base(),
                div_reg = self.get_register_file().get_div_register(),
                freq_path = freq_path,
            )
        with open(bmk_src, "w") as bmkfile:
            bmkfile.write(program)

        # compile src file to bin file
        compile_cmd = [self.settings.cc, bmk_src, "-fomit-frame-pointer", "-o", bmk_bin]
        if self.additional_cc_flags is not None:
            compile_cmd += self.additional_cc_flags
        rc = subprocess.call(compile_cmd)
        if rc != 0:
            print('  compilation failed!')
            return { 'cycles': None, 'error_cause': "compilation failed" }

        # run bin file
        command = self.create_command(bmk_bin)

        rv = subprocess.run(command, stdout=subprocess.PIPE)

        if rv.returncode != 0:
            print('  execution failed!')
            return { 'cycles': None, 'error_cause': "execution failed" }
        str_res = rv.stdout.decode("utf-8")

        return self.extract_result(str_res, num_testcase_instances)

    def create_command(self, bmk_bin):
        command = []
        if which("taskset") is not None:
            command += ["taskset", "-c", str(self.settings.core)]
        command.append(bmk_bin)
        return command

    def extract_result(self, str_res, num_testcase_instances):
        json_dict = json.loads(str_res)
        return {
                'benchtime': float(json_dict['benchtime']),
                'cycles': float(json_dict['cycles']),
                'meas_freq': int(json_dict['meas_freq'])
            }

    def __get_description__(self):
        search_dir = os.path.join(self.settings.input_dir, self.dirname)
        filenames = []
        self.instruction_list = []
        self.insnmap = dict()
        for root, dirs, files in os.walk(search_dir):
            for infile in files:
                if infile.endswith(".insn"):
                    filenames.append(os.path.join(root, infile))

        for filename in filenames:
            self.instruction_list += parse_instructionlist(filename)
        for i in self.instruction_list:
            self.insnmap[str(i)] = i

    @abstractmethod
    def init_code_for_register(self, reg):
        pass

    # The unfinished version of the program that executes the experiments
    # with placeholders for parameters
    program_frame = """\
#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <dlfcn.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <string.h>

{INCLUDES}

int main (void) {{
    struct timeval start, end;
    double benchtime;
    // allocate and initialize scratch memory for loads and stores
    long long mem_size = 4096 + 32768;
    char * memt = (char*) aligned_alloc(4096, mem_size);
    for (int i = 0; i < mem_size; ++i) {{
        memt[i] = 42;
    }}
    long long N = {num_iterations};
    double freq = {frequency};
    long long num_instances_per_iteration = {num_instances_per_iteration};

    // initialization code
{ASM_INIT}

    {{ // Warmup Code
    register void * mem asm("{membasereg}") = memt + 4096;
    register long long div asm("{div_reg}") = 44; // initialize the non-zero divisor register
{WARMUP_CODE}
    }}

    FILE* f = fopen("{freq_path}", "r");
    long long meas_freq;
    fscanf(f, "%lld", &meas_freq);
    fclose(f);

    freq = (double)meas_freq;

    gettimeofday(&start, NULL);

    register void * mem asm("{membasereg}") = memt + 4096;
    register long long div asm("{div_reg}") = 44; // initialize the non-zero divisor register

    // ASM loop
{ASM_INSTRUCTIONS}

    gettimeofday(&end, NULL);

    // dump output
    fprintf (stdout, "{{\\n");
    // This returns the time for the experiment in microseconds (1e(-6)s)
    benchtime = ((double)end.tv_sec - (double)start.tv_sec) * 1000000 + ((double)end.tv_usec - (double)start.tv_usec);
    fprintf(stdout, "  \\"benchtime\\": %.2f,\\n", benchtime);

    // calculate cycles per Testcase: time * e(-6) * freq * e3 / n
    double instruction_throughput = (benchtime * freq) / ((double)N * num_instances_per_iteration * 1000.0);
    fprintf(stdout, "  \\"cycles\\": %.10f,\\n", instruction_throughput);
    fprintf(stdout, "  \\"meas_freq\\": %lld\\n", meas_freq);
    fprintf(stdout, "}}\\n");
}}
   """

