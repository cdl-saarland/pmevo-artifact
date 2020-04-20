#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

import argparse
import json
import random
import sys

from utils.evo_algo_wrapper import Inferrer
from utils.experiment import ExperimentList


def main():
    argparser = argparse.ArgumentParser(description='Infer a portmapping for a list of experiments')
    argparser.add_argument('config', metavar='CFG', help='inferrer config in json format to use')
    argparser.add_argument('exps', metavar='EXPFILE', help='path to file with experiments')
    argparser.add_argument('--singletonexps', metavar='EXPFILE', default=None, help='path to file with experiments')
    argparser.add_argument('-o', '--out', metavar='OUTFILE', default=None, help='path to file to write the resulting data to')
    argparser.add_argument('--seed', metavar='N', type=int, default=73737, help='specify a seed for the RNG')
    args = argparser.parse_args()
    random.seed(args.seed)

    with open(args.exps, "r") as exps_file:
        explist = ExperimentList.from_json(exps_file)

    if args.singletonexps is not None:
        with open(args.singletonexps, "r") as add_exps_file:
            add_explist = ExperimentList.from_json(add_exps_file)
        explist.exps.extend(add_explist.exps)

    with open(args.config, 'r') as config_file:
        config = json.load(config_file)

    inf = Inferrer.from_config(config)

    mapping = inf.infer(explist)

    if mapping is None:
        print("Failed to infer mapping!", file=sys.stderr)
        exit(1)

    if args.out is not None:
        with open(args.out, "w") as outfile:
            mapping.to_json(outfile)

    print(mapping)
    exit(0)


if __name__ == "__main__":
    main()
