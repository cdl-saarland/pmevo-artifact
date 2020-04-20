#!/usr/bin/env python3

from utils.architecture import Architecture
from utils.mapping import Mapping3
from utils.experiment import ExperimentList

from utils.jsonable import Vault

from processors.processor import Processor

import utils.evo_algo_wrapper as evo_algo

import argparse
import os
import shutil

def main():
    argparser = argparse.ArgumentParser(description='Compare the running time of different mapping simulators')

    argparser.add_argument('-o', '--out', metavar='FILE', default="sim_time.json", help='name of file to print json data to')
    argparser.add_argument('cppbuild', metavar='PATH', help='path to the cpp-evolution build folder')
    argparser.add_argument('--explen', action='store_true', help='test experiment length instead of port number')
    argparser.add_argument('--full', action='store_true', help='use the full evaluation configuration from the paper')

    args = argparser.parse_args()

    if args.full:
        min_num_ports = 4
        max_num_ports = 20
        num_insns = 100
        num_exps = 128
        num_mappings = 8
        num_insns_per_exp = 5
        num_repetitions = 1000
    else:
        min_num_ports = 4
        max_num_ports = 20
        num_insns = 100
        num_exps = 8
        num_mappings = 4
        num_insns_per_exp = 5
        num_repetitions = 200

    simulators = {
        "lp via z3": os.path.expanduser("{}/z3/pm-evo".format(args.cppbuild)),
        "bottleneck algorithm": os.path.expanduser("{}/default-pm-evo".format(args.cppbuild)),
        # "lpsingle": os.path.expanduser("{}/gurobi_single/pm-evo".format(args.cppbuild)),
    }

    v = Vault(args.out)

    v.add(simulators)

    # proc_cls = Processor.get_default_cls()
    proc_cls = Processor.class_for_name("cppbottleneck")

    if not args.explen:
        arch = Architecture()
        arch.add_insns(["i{:3}".format(i) for i in range(num_insns)])
        for n in range(num_exps):
            print("experiment {} out of {}".format(n + 1, num_exps))
            el = ExperimentList(arch)
            el.insert_random_exp(num_insns_per_exp)
            for num_ports in range(min_num_ports, max_num_ports+1):
                # print("num_ports: {}".format(num_ports))
                arch.ports.clear()
                arch.add_number_of_ports(num_ports)
                for nm in range(num_mappings):
                    m = Mapping3.from_random(arch=arch, num_uops_per_insn=6)

                    # make a reference evaluation of el with m
                    proc = proc_cls(m)
                    proc.eval_list(el)

                    results = {}
                    # test m, el with all simulators
                    for ident, sim_path in simulators.items():
                        results[ident] = evo_algo.evaluateExperiments(sim_path, m, el, num_repetitions=num_repetitions)

                    # store all data
                    entry = {
                        "arch_info": {
                            "num_insns": num_insns,
                            "num_ports": num_ports,
                            },
                        "mapping": m,
                        "exp_idx": n,
                        "exps": el,
                        "measured_secs_per_exp": results,
                    }
                    v.add(entry)
    else:
        if args.full:
            num_ports = 10
        else:
            num_ports = 8
        arch = Architecture()
        arch.add_insns(["i{:3}".format(i) for i in range(num_insns)])
        arch.add_number_of_ports(num_ports)
        min_num_insns_per_exp = 1
        max_num_insns_per_exp = 10
        num_exps = max_num_insns_per_exp + 1 - min_num_insns_per_exp
        for x, num_insns_per_exp in enumerate(range(min_num_insns_per_exp, max_num_insns_per_exp+1)):
            print("experiment {} out of {}".format(x + 1, num_exps))
            for n in range(num_exps):
                el = ExperimentList(arch)
                el.insert_random_exp(num_insns_per_exp)
                for nm in range(num_mappings):
                    m = Mapping3.from_random(arch=arch, num_uops_per_insn=6)

                    # make a reference evaluation of el with m
                    proc = proc_cls(m)
                    proc.eval_list(el)

                    results = {}
                    # test m, el with all simulators
                    for ident, sim_path in simulators.items():
                        results[ident] = evo_algo.evaluateExperiments(sim_path, m, el, num_repetitions=num_repetitions)

                    # store all data
                    entry = {
                        "arch_info": {
                            "num_insns": num_insns,
                            "num_ports": num_ports,
                            },
                        "mapping": m,
                        "exp_idx": n,
                        "exps": el,
                        "num_insns_per_exp": num_insns_per_exp,
                        "measured_secs_per_exp": results,
                    }
                    v.add(entry)

    v.finalize()

if __name__ == "__main__":
    main()
