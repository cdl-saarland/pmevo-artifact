#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

import argparse

import datetime
import re
import sys

from utils.mapping import Mapping
from utils.experiment import ExperimentList
from processors.processor import Processor
from processors.remote_processor import RemoteProcessor

from utils.client import add_client_args

def main():
    argparser = argparse.ArgumentParser(description='Evaluate experiment list with a mapping or remote processor and annotate results to experiment list')

    argparser.add_argument('-m', '--mapping', metavar='FILE', default=None, help='input mapping in json format')
    argparser.add_argument('-x', '--identifier', metavar="ID", required=True, help='unique identifier of the used processor for adding into the experiment list')
    argparser.add_argument('-o', '--out', metavar="FILE", default=None, help='name for the resulting output experiment lists')
    argparser.add_argument('exps', metavar='FILE', nargs='+', help='input experiment list in json format')

    add_client_args(argparser)

    args = argparser.parse_args()

    identifier = args.identifier

    if args.mapping is not None:
        with open(args.mapping, 'r') as infile:
            m = Mapping.read_from_json(infile)

        # proc = Processor.get_default_cls()(m)
        proc = Processor.class_for_name("cppbottleneck")(m)

    else:
        proc = RemoteProcessor(hostname=args.host, port=args.port, sslpath=args.sslpath)

    arch = proc.get_arch()

    for exps in args.exps:
        with open(exps, 'r') as infile:
            elist = ExperimentList.from_json(infile, arch)

        present_ids = [ ores["id"] for ores in elist.exps[0].other_results ]
        if identifier in present_ids:
            print("Error: The ExperimentList in {} already contains measurements with the tag {}!".format(exps, identifier), file=sys.stderr)
            sys.exit(1)

        percentage_step = 10
        next_percentage = 0
        num_exps = len(elist.exps)
        print("Evaluating experiments from {} with a {}...".format(exps, proc.get_description()))
        for x, e in enumerate(elist):
            if x * 100 / num_exps >= next_percentage:
                print("  {}%".format(next_percentage))
                next_percentage += percentage_step
            result = proc.execute(e.iseq)
            result["id"] = identifier
            result["creation_date"] = datetime.datetime.now().isoformat()
            e.other_results.append(result)
        print("Done evaluating experiments from {}.".format(exps))

        if args.out is not None:
            outname = args.out
        else:
            inname = exps
            if inname.endswith(".json"):
                outname = inname[:-len(".json")]
            else:
                outname = inname

            mat = re.search("_eval(\d+)$", outname)
            if mat is not None:
                num = mat.group(1)
                outname = outname[:-len(num)]
                outname = outname + "{:02}".format(int(num)+1)
            else:
                outname += "_eval01"

            outname += ".json"

        with open(outname, "w") as outfile:
            elist.to_json(outfile)

if __name__ == "__main__":
    main()
