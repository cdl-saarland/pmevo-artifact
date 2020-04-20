#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

import argparse
from utils.experiment import ExperimentList


def main():
    argparser = argparse.ArgumentParser(description='Merge the other_result entries of experiment lists with identical experiments')

    argparser.add_argument('-o', '--out', metavar="FILE", required=True, help='name for the resulting output experiment list')
    argparser.add_argument('exps', metavar='FILE', nargs='+', help='input experiment lists in json format')

    args = argparser.parse_args()


    with open(args.exps[0], 'r') as infile:
        elist = ExperimentList.from_json(infile)

    for inpath in args.exps[1:]:
        with open(inpath, 'r') as infile:
            other_elist = ExperimentList.from_json(infile)
        for e, other_e in zip(elist.exps, other_elist.exps):
            for i1, i2 in zip(e.iseq, other_e.iseq):
                assert i1.name == i2.name
            present_ids = [ r["id"] for r in e.other_results ]
            for r in other_e.other_results:
                ident = r["id"]
                if ident in present_ids:
                    continue
                e.other_results.append(r)

    with open(args.out, "w") as outfile:
        elist.to_json(outfile)


if __name__ == "__main__":
    main()
