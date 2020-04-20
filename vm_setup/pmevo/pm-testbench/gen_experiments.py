#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

import argparse
import itertools
import math
import random
import sys

from processors.remote_processor import RemoteProcessor
from utils.client import add_client_args
from utils.jsonable import Vault, filename_append
from utils.experiment import ExperimentList
from utils.sample_experiments import sample_experiments
from utils.partition_insns import create_partition

def strip_results(elist, key):
    for e in elist:
        if key in e.result:
            del(e.result[key])

def main():
    default_repetitions = 5
    default_target_time_us = 10000
    default_num_insns_per_iteration = 100
    default_epsilon = 0.1

    argparser = argparse.ArgumentParser(description='Generate experiments and execute them on a remote server')
    add_client_args(argparser)
    argparser.add_argument('-r', '--repetitions', metavar='N', type=int, default=default_repetitions,
            help='take the minimum over N repetitions for each experiment (default: {})'.format(default_repetitions))
    argparser.add_argument('-t', '--targettime', metavar='T', type=float, default=default_target_time_us,
            help='target time to run each experiment in microseconds (default: {})'.format(default_target_time_us))
    argparser.add_argument('-n', '--insnsperiteration', metavar='N', type=int, default=default_num_insns_per_iteration,
            help='Number of instructions per loop iteration (default: {})'.format(default_num_insns_per_iteration))
    argparser.add_argument('out', metavar='OUTFILE',
            help='path to file to write the resulting list of experiments to')
    argparser.add_argument('--seed', metavar='S', type=int, default=424242,
            help='seed for random number generator (default: {})'.format(424242))
    argparser.add_argument('--vault', metavar="FILE", default=None,
            help="name of a file to use for storing intermediate results")
    argparser.add_argument('--eval', metavar=["NUM", "MIN", "MAX"], nargs=3, default=None, help="generate NUM uniformly sampled evaluation tests with a length between MIN and MAX")
    argparser.add_argument('--step', metavar=["NUM", "MIN", "MAX"], nargs=3, default=None, help="for each length between MIN and MAX, generate NUM uniformly sampled evaluation tests with that length")
    argparser.add_argument('--exps', metavar='FILE', default=None,
            help='experiment list in json format to evaluate instead of new random tests')
    argparser.add_argument('-v', '--verbose', action='store_true', help='do not strip additional metadata from experiments before writing')
    argparser.add_argument('-e' , '--epsilon', metavar='E', type=float, default=default_epsilon, help='maximal difference of values to count as equal (default: {})'.format(default_epsilon))

    args = argparser.parse_args()

    if args.step is not None and args.eval is not None:
        print("Do only provide at least one of --step and --eval!", file=sys.stderr)
        sys.exit(1)

    random.seed(args.seed)

    proc = RemoteProcessor(hostname=args.host, port=args.port, sslpath=args.sslpath)
    arch = proc.get_arch()

    vault = None
    if args.vault is not None:
        vault = Vault(args.vault)

    insns = arch.insn_list()


    dropped_runs = []

    prog_id = 0
    def eval_elist(elist):
        nonlocal prog_id, dropped_runs
        for x, e in enumerate(elist, start=1):
            print("Running experiment {curr} of {num}: {exp}".format(curr=x, num=len(elist.exps), exp=repr(e)))
            res = proc.execute(e.iseq,
                    repetitions = args.repetitions,
                    target_time_us = args.targettime,
                    num_insns_per_iteration = args.insnsperiteration,
                    max_uncertainty = args.epsilon * 0.5)
            e.result = res
            if res["cycles"] is None:
                print("Failed to evaluate an experiment:", file=sys.stderr)
                print("  experiment: {}".format(repr(e)), file=sys.stderr)
                print("  result: {}".format(e.get_result()), file=sys.stderr)
                sys.exit(1)
            if len(res["invalid_runs"]) > 0:
                dropped_runs.append(res["invalid_runs"])
            print("  Result: {}".format(e.get_result()))
            if vault is not None:
                vault.add(e, progress_id=prog_id)
                prog_id += 1

    if args.step is not None:
        num, minl, maxl = map(int, args.step)
        insns = arch.insn_list()
        # insns = [ i for i in arch.insn_list() if not i.name.startswith("BT")]
        for curr_len in range(minl, maxl):
            elist = ExperimentList(arch)
            experiments = sample_experiments(insns, curr_len, curr_len + 1, num)
            for iseq in experiments:
                elist.create_exp(iseq)
            eval_elist(elist)

            if not args.verbose:
                strip_results(elist, "valid_runs")
                strip_results(elist, "invalid_runs")

            outname = filename_append(args.out, "_len_{:02d}".format(curr_len))
            with open(outname, "w") as outfile:
                elist.to_json(outfile)

        if vault is not None:
            vault.finalize(False)
        return

    if args.eval is not None:
        insns = arch.insn_list()
        outfilename = args.out

        if args.exps is not None:
            with open(args.exps, 'r') as infile:
                elist = ExperimentList.from_json(infile)
            num = len(elist.exps)
        else:
            num, minl, maxl = map(int, args.eval)
            elist = ExperimentList(arch)

            print("Sampling {num} evaluation experiments with length between {minl} and {maxl}...".format(num=num, minl=minl, maxl=maxl))
            experiments = sample_experiments(insns, minl, maxl, num)
            for iseq in experiments:
                elist.create_exp(iseq)

            with open(outfilename, "w") as outfile:
                elist.to_json(outfile)
            print("Written {} sampled evaluation experiments to {}.".format(len(elist.exps), outfilename))

        print("Running {num} evaluation experiments...".format(num=num))
        eval_elist(elist)
        if not args.verbose:
            strip_results(elist, "valid_runs")
            strip_results(elist, "invalid_runs")

        with open(outfilename, "w") as outfile:
            elist.to_json(outfile)
        print("Written {} evaluated evaluation experiments to {}.".format(len(elist.exps), outfilename))

        print("Dropped runs for {} experiments because of unstable clock frequency:".format(len(dropped_runs)))
        for r in dropped_runs:
            print("  {}".format(r))

        if vault is not None:
            vault.finalize(False)

        return

    pair_file = filename_append(args.out, "_pair")
    singleton_file = filename_append(args.out, "_singletons")

    # generate singleton experiments
    print("Generating {} singleton experiments...".format(len(insns)))
    singleton_elist = ExperimentList(arch)
    singleton_map = dict()

    for i in insns:
        exp = singleton_elist.create_exp([i])
        singleton_map[i] = exp

    with open(singleton_file, "w") as outfile:
        singleton_elist.to_json(outfile)

    print("Written {} singleton experiments to {}.".format(len(insns), singleton_file))

    # evaluate singleton experiments
    print("Evaluating {} singleton experiments...".format(len(insns)))

    eval_elist(singleton_elist)

    if not args.verbose:
        strip_results(singleton_elist, "valid_runs")
        strip_results(singleton_elist, "invalid_runs")

    with open(singleton_file, "w") as outfile:
        singleton_elist.to_json(outfile)

    print("Written {} evaluated singleton experiments to {}.".format(len(insns), singleton_file))

    epsilon = args.epsilon

    def equals(a, b):
        return abs(a - b) <= epsilon

    singleton_results = dict()
    for e in singleton_elist:
        assert len(e.iseq) == 1
        i = e.iseq[0]
        t = e.get_cycles()
        singleton_results[i] = t

    singleton_equiv_map = { (i, j): equals(singleton_results[i], singleton_results[j]) for (i, j) in itertools.combinations(insns, 2) }

    # Partition the instructions according to equivalent singleton results and
    # use the maximal occuring singleton result of the class of equivalent
    # instructions. This is needed so that equivalent instructions get
    # corresponding experiments with identical sizes so that these experiments
    # can be used for preprocessing later on.
    insn_buckets, insn_to_bucket = create_partition(insns, singleton_equiv_map)
    insn_to_max_t = { i: max(( singleton_results[j] for j in b )) for i, b in insn_to_bucket.items() }

    # generate pair experiments
    print("Generating pair experiments...")
    pair_elist = ExperimentList(arch)

    for i, j in itertools.combinations(insns, 2):
        pair_elist.create_exp([i, j])
        ti = insn_to_max_t[i]
        tj = insn_to_max_t[j]
        if ti < tj:
            i, j = j, i
            ti, tj = tj, ti
        factor = math.ceil(ti / tj)
        if factor == 1:
            continue
        iseq = [i]
        iseq += [j for x in range(factor)]
        pair_elist.create_exp(iseq)


    with open(pair_file, "w") as outfile:
        pair_elist.to_json(outfile)

    print("Written {} pair experiments to {}.".format(len(pair_elist.exps), pair_file))

    # evaluate pair experiments

    print("Evaluating {} pair experiments...".format(len(pair_elist.exps)))

    eval_elist(pair_elist)

    if not args.verbose:
        strip_results(pair_elist, "valid_runs")
        strip_results(pair_elist, "invalid_runs")

    with open(pair_file, "w") as outfile:
        pair_elist.to_json(outfile)

    print("Written {} evaluated pair experiments to {}.".format(len(pair_elist.exps), pair_file))

    print("Dropped runs for {} experiments because of unstable clock frequency:".format(len(dropped_runs)))
    for r in dropped_runs:
        print("  {}".format(r))

    if vault is not None:
        vault.finalize(False)

if __name__ == "__main__":
    main()

