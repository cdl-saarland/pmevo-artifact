# vim: et:ts=4:sw=4:fenc=utf-8

import json
import os
import time
import math


def get_machine_dependent_params(settings, isa):
    if os.path.isfile(settings.machine_dependent_params_file) and not settings.newSU:
        with open(settings.machine_dependent_params_file, "r") as params_file:
            params = json.load(params_file)
        settings.num_total_dynamic_insns = params["num_total_dynamic_insns"]
        settings.num_insns_per_iteration = params["num_insns_per_iteration"]
    else:
        assert len(isa.instruction_list) > 4, 'At least 5 instructions are required per isa!'
        settings.num_total_dynamic_insns = determine_num_total_dynamic_insns(settings, isa)
        settings.num_insns_per_iteration = determine_num_insns_per_iteration(settings, isa)
        params = {
                "num_total_dynamic_insns": settings.num_total_dynamic_insns,
                "num_insns_per_iteration": settings.num_insns_per_iteration,
            }
        if os.path.isfile(settings.machine_dependent_params_file):
            # If we have a previously existing param file, create a backup
            os.rename(settings.machine_dependent_params_file, settings.machine_dependent_params_file + ".bak")

        with open(settings.machine_dependent_params_file, "w") as params_file:
            json.dump(params, params_file)

    print("Configured to run {} dynamic instructions in a loop with {} instructions per iteration.".format(
        settings.num_total_dynamic_insns, settings.num_insns_per_iteration))

def determine_num_total_dynamic_insns(settings, isa):
    from PITE.processor_benchmarking import run_experiment_impl
    num_insns_per_iteration = 200
    rangeX = 11
    insns = sorted(isa.insnmap.keys())

    testing_num_total_dynamic_insns = 10**9

    print("Starting to determine the total number of dynamic instructions necessary to execute for {} seconds.".format(settings.loop_target_time))

    min_time = math.inf
    for i in insns[0:5]:
        tmp_results = []
        for j in range(rangeX):
            tmp_results.append(run_experiment_impl(settings, isa, [i],
                num_insns_per_iteration=num_insns_per_iteration,
                num_total_dynamic_insns=testing_num_total_dynamic_insns))
        time_taken = sum(float(x['benchtime']) / 1000000 for x in tmp_results) / rangeX
        min_time = min(min_time, time_taken)

    num_total_dynamic_insns = int((settings.loop_target_time / min_time) * testing_num_total_dynamic_insns)

    print("Determine the total number of dynamic instructions to be {}.".format(num_total_dynamic_insns))

    return num_total_dynamic_insns

def determine_num_insns_per_iteration(settings, isa):
    # This requires a reasonable num_total_dynamic_insns in the settings!
    print("Starting to determine the number of instructions per iteration for this machine.")
    startLLMeasuring = time.perf_counter()

    assert isa.insnmap is not None
    if settings.preciseStart:
        config = settings.setup_configs["precise"]
    else:
        config = settings.setup_configs["default"]

    inital_looplength = config["start_loop_length"]
    final_looplength = config["end_loop_length"]
    num_total_dynamic_insns = settings.num_total_dynamic_insns
    steps = config["step_width"]
    fg_steps = config["fine_grained_step_width"]
    num_samples = config["num_samples"]

    minLength = __exec_experiments(settings, isa, inital_looplength, final_looplength, steps, num_total_dynamic_insns, num_samples)

    # adjustment so that fine-grained searching can start at minLength - steps
    minLength = max(minLength, inital_looplength + steps)

    print('Determined number of instructions per iteration to be around {}'.format(minLength))
    minLength = __exec_experiments(settings, isa, minLength - steps, minLength + steps, fg_steps, num_total_dynamic_insns, num_samples)
    print('Number of instructions per iteration fixed at: {}'.format(minLength))
    res = minLength

    endLLMeasuring = time.perf_counter()
    timeLL = endLLMeasuring - startLLMeasuring
    print("Done determining the number of iterations after {} seconds.".format(timeLL))
    return res

def __exec_experiments(settings, isa, inital_ll, final_ll, steps_width, num_total_dynamic_insns, num_samples):
    from PITE.processor_benchmarking import run_experiment_impl
    assert isa.insnmap is not None
    insns = sorted(isa.insnmap.keys())
    results = []
    for i in range(inital_ll, final_ll, steps_width):
        intermed_res = []
        for j in range(num_samples):
            tmp_res = run_experiment_impl(settings, isa, insns[0:5], num_insns_per_iteration=i, num_total_dynamic_insns=num_total_dynamic_insns)
            intermed_res.append(tmp_res)
        i_res = min(intermed_res, key=lambda t: t['cycles'])
        results.append((i, i_res['cycles']))
    minLength = min(results, key=lambda t: t[1])
    return minLength[0]

