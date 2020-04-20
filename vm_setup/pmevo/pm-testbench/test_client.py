#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

import argparse
import itertools
import re

from processors.remote_processor import RemoteProcessor
from utils.experiment import Experiment, ExperimentList
from utils.client import add_client_args

def main():
    default_length = 1
    default_repetitions = 1
    argparser = argparse.ArgumentParser(description='Test a remote server')
    add_client_args(argparser)
    argparser.add_argument('-l', '--length', metavar='N', type=int, default=default_length,
            help='test all experiments of length up to N (default: {})'.format(default_length))
    argparser.add_argument('-r', '--repetitions', metavar='N', type=int, default=default_repetitions,
            help='execute each experiment N times on the server (default: {})'.format(default_repetitions))
    argparser.add_argument('-f', '--filter', metavar='STR', default=None,
            help='only use instructions whose name contains STR')
    argparser.add_argument('-x', '--regex', metavar='RE', default=None,
            help='only use instructions whose name contains a match for RE')
    argparser.add_argument('-n', '--num', metavar='N', type=int, default=-1,
            help='execute only the first N experiments per length (default: -1)')

    args = argparser.parse_args()

    proc = RemoteProcessor(hostname=args.host, port=args.port, sslpath=args.sslpath)
    arch = proc.get_arch()

    print("Remote processor supports {} instructions and has {} ports.".format(len(arch.insns), len(arch.ports)))

    elist = ExperimentList(arch)

    insns = arch.insn_list()

    if args.filter is not None:
        insns = filter(lambda x: args.filter in x.name, insns)

    if args.regex is not None:
        insns = filter(lambda x: re.search(args.regex, x.name) is not None, insns)

    for l in range(1, args.length + 1):
        print("Running experiments of length {}...".format(l))
        for x, iseq in enumerate(itertools.combinations_with_replacement(insns, l)):
            if args.num > 0 and x >= args.num:
                break
            e = Experiment(arch, iseq)
            elist.insert_exp(e)
            res = proc.execute(e.iseq, repetitions=args.repetitions, target_time_us=500000, num_insns_per_iteration=10)
            e.result = res
            print(repr(e))

    ranking = []

    failing_exps = []
    for e in elist:
        if e.get_cycles() is None:
            failing_exps.append(e)
        else:
            ranking.append( (e.iseq[0], e.get_cycles()) )

    if len(failing_exps) > 0:
        print("Some experiments failed:")
        for e in failing_exps:
            print("  {}".format(repr(e)))


    # print(elist)

if __name__ == "__main__":
    main()
