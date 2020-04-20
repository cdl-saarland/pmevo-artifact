# vim: et:ts=4:sw=4:fenc=utf-8

import math
import random
import subprocess
from abc import ABC, abstractmethod
from statistics import median

from PITE.register_allocation import Allocator

# This is the interface that a benchmark runner has to implement to be used in
# a benchmarking server.
class LowLevelEvaluator(ABC):
    @abstractmethod
    def get_insns(self):
        """ Return an iterable containing unique identifiers of instructions.
        """
        pass

    @abstractmethod
    def get_num_ports(self):
        """ Return the number of ports available.
        """
        pass

    @abstractmethod
    def run_experiment(self, exp):
        """ Executes the experiment denoted by exp, an iterable of instruction
            identifiers (as obtained via get_insns) and returns a dictionary
            with results including the number of cycles required under the
            'cycles' key.
        """
        pass

    @abstractmethod
    def gen_code(self, exp, **kwargs):
        pass

    @abstractmethod
    def get_description(self):
        pass


def __read_frequency(settings):
    """ Read the current clock frequency of the benchmarked core. Only supported
        when executed with root privileges.
    """
    if settings.no_root:
        return -1.0
    with open(settings.scaling_freq.format(core=settings.core), "r") as current_freq:
        return float(current_freq.readline())


class PITELLEval(LowLevelEvaluator):

    def __init__(self, settings, isa, num_ports, freq_setter=None):
        self.settings = settings
        self.isa = isa
        self.instruction_list = sorted(self.isa.insnmap.keys())
        self.freq_setter = freq_setter
        self.num_ports = num_ports

    def get_insns(self):
        return self.instruction_list

    def get_num_ports(self):
        return self.num_ports

    def gen_code(self, exp, **kwargs):
        run_params = self.get_run_parameters(
                exp = exp,
                num_insns_per_iteration = kwargs.get('num_insns_per_iteration', None),
                num_total_dynamic_insns = kwargs.get('num_total_dynamic_insns', None),
                target_time_us = kwargs.get('target_time_us', None),
            )
        if run_params[0] is None:
            return run_params[1] # error information

        num_insns_per_iteration, num_total_dynamic_insns = run_params
        repetitions = kwargs.get('repetitions', self.settings.default_num_repetitions)
        max_uncertainty = kwargs.get('max_uncertainty', self.settings.default_max_uncertainty)

        testcase = [ self.isa.insnmap[insn] for insn in exp ]

        num_testcase_instances = math.ceil(num_insns_per_iteration / len(testcase))

        loop = []
        for i in range(num_testcase_instances):
            for insnform in testcase:
                loop.append(insnform.get_instance())

        alloc = Allocator(self.isa) # TODO move out?
        alloc.allocate_registers(loop)

        res_str = "\n".join([ i.get_str() for i in loop])
        return res_str, num_testcase_instances

    def run_experiment(self, exp, **kwargs):
        run_params = self.get_run_parameters(
                exp = exp,
                num_insns_per_iteration = kwargs.get('num_insns_per_iteration', None),
                num_total_dynamic_insns = kwargs.get('num_total_dynamic_insns', None),
                target_time_us = kwargs.get('target_time_us', None),
            )
        if run_params[0] is None:
            return run_params[1] # error information

        num_insns_per_iteration, num_total_dynamic_insns = run_params
        repetitions = kwargs.get('repetitions', self.settings.default_num_repetitions)
        max_uncertainty = kwargs.get('max_uncertainty', self.settings.default_max_uncertainty)

        def run(intermed_res, repetitions, num_insns_per_iteration):
            for j in range(repetitions):
                curr_exp = exp[:]
                tmp_res = run_experiment_impl(self.settings, self.isa, exp,
                        num_insns_per_iteration=num_insns_per_iteration,
                        num_total_dynamic_insns=num_total_dynamic_insns)
                intermed_res.append(tmp_res)

        intermed_res = []
        run(intermed_res, repetitions, num_insns_per_iteration)

        for r in intermed_res:
            if r["cycles"] is None:
                return r

        valid_res = [ r for r in intermed_res if r["tp_uncertainty"] < max_uncertainty ]
        invalid_res = [ r for r in intermed_res if r["tp_uncertainty"] >= max_uncertainty ]

        res = dict()

        if len(valid_res) <= repetitions // 2:
            # we consider measurements as too unreliable if half of them are not precise enough
            res['cycles'] = None
            res['error_cause'] = "frequency too unreliable for measurements, try more repetitions"
        else:
            res['cycles'] = median(map(lambda t: t['cycles'], valid_res))
            # res['cycles'] = min(map(lambda t: t['cycles'], valid_res))

        res['valid_runs'] = valid_res
        res['invalid_runs'] = invalid_res
        return res

    def get_description(self):
        return "PITE ({}) processor".format(self.isa.name)

    def get_run_parameters(self, exp, num_insns_per_iteration, num_total_dynamic_insns, target_time_us):
        if self.isa.is_simulated():
            if num_insns_per_iteration is None:
                num_insns_per_iteration = self.settings.num_insns_per_iteration
            if num_total_dynamic_insns is None:
                num_total_dynamic_insns = self.settings.num_total_dynamic_insns
            return num_insns_per_iteration, num_total_dynamic_insns
        # take the default if no number of instruction instances per iteration
        # is given
        if (num_insns_per_iteration is None):
            num_insns_per_iteration = self.settings.num_insns_per_iteration

        # when a target time is given, run a test experiment and use its
        # execution time to estimate the right number of dynamic instructions
        # to execute in the loop
        if target_time_us is not None:
            assert num_total_dynamic_insns is None, "Cannot set target_time_us and num_total_dynamic_insns together!"
            test_num_dyn = self.settings.num_total_dynamic_insns // 20
            tmp_res = run_experiment_impl(self.settings, self.isa, exp,
                    num_insns_per_iteration=num_insns_per_iteration,
                    num_total_dynamic_insns=test_num_dyn)
            if tmp_res['cycles'] == None:
                return (None, tmp_res)
            default_time = tmp_res['benchtime']
            num_total_dynamic_insns = round((test_num_dyn * target_time_us) / default_time)

        # if not specified or implied by a target time, use the default
        # total number of dynamic instructions
        if (num_total_dynamic_insns is None):
            num_total_dynamic_insns = self.settings.num_total_dynamic_insns

        return num_insns_per_iteration, num_total_dynamic_insns

def run_experiment_impl(settings, isa, exp, num_insns_per_iteration, num_total_dynamic_insns):
    testcase = [ isa.insnmap[insn] for insn in exp ]

    frequency = __read_frequency(settings)

    print('running experiment:')
    for i in testcase:
        print("    {}".format(i))
    print("  at {} kHz".format(frequency))
    print("  with {} total dynamic instructions".format(num_total_dynamic_insns))
    print("  in a loop with {} instructions per iteration".format(num_insns_per_iteration))

    num_testcase_instances = math.ceil(num_insns_per_iteration / len(testcase))

    loop = []
    for i in range(num_testcase_instances):
        for insnform in testcase:
            loop.append(insnform.get_instance())

    alloc = Allocator(isa) # TODO move out?
    alloc.allocate_registers(loop)

    actual_num_insns_per_iteration = len(loop)
    num_iterations = num_total_dynamic_insns // actual_num_insns_per_iteration

    bmk_src = settings.benchmark_src

    result = isa.compile_and_run(
            iseq = loop,
            cpufreq = frequency,
            num_iterations = num_iterations,
            num_testcase_instances = num_testcase_instances,
            freq_path = settings.scaling_freq.format(core=settings.core),
        )

    print('  output: {}'.format(result))

    if isa.is_simulated():
        result["tp_uncertainty"] = 0.0
        return result

    frequency_after = __read_frequency(settings)
    print('  frequency after experiment: {}'.format(frequency_after))
    print('  frequency difference: {}'.format(abs(frequency_after - frequency)))

    tp_freq_before = (result["benchtime"] * frequency) / (num_iterations * num_testcase_instances * 1000)
    tp_freq_after = (result["benchtime"] * frequency_after) / (num_iterations * num_testcase_instances * 1000)

    print('  throughput with before frequency: {}'.format(tp_freq_before))
    print('  throughput with after frequency: {}'.format(tp_freq_after))
    error = 2 * abs(tp_freq_before - tp_freq_after) / (tp_freq_before + tp_freq_after)
    print('  error: {:4.2f}%'.format(error * 100))

    result["freq_before"] = frequency
    result["freq_after"] = frequency_after
    result["tp_before"] = tp_freq_before
    result["tp_after"] = tp_freq_after
    result["tp_uncertainty"] = error

    return result

