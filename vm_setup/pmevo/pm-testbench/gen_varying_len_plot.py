#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

import argparse
import datetime
import json
from utils.experiment import ExperimentList

import os.path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from numpy import mean

import utils.plot_utils as pu

def configure_plot(size=None):
    if size is not None:
        plt.figure(figsize=size)
    sns.set(style="whitegrid")
    paper_rc = {'lines.linewidth': 0.8,
            'axes.edgecolor': 1.0,
            }
    sns.set_context('paper', rc=paper_rc)

def main():
    default_report = os.path.expanduser("~/reports/var_len_report.json")
    argparser = argparse.ArgumentParser(description='Crunch the other_result entries of an experiment lists for statistics and plots')

    argparser.add_argument('-x', '--identifier', metavar="ID", default=None, help='only consider other_results with this identifier')
    argparser.add_argument('exps', metavar='FILE', nargs='+', help='input experiment list(s) in json format')
    argparser.add_argument('-r', '--report', metavar='OUTFILE', default=default_report, help='name of a file to write a report file to (default: {})'.format(default_report))

    args = argparser.parse_args()

    acc_results = []

    for elist_file in args.exps:
        with open(elist_file, 'r') as infile:
            elist = ExperimentList.from_json(infile)

        exp_len = len(elist.exps[0].iseq)

        ref_cycles_list = []

        other_results = dict()

        for e in elist:
            ref_cycles = e.get_cycles()
            ref_cycles_list.append(ref_cycles)
            for r in e.other_results:
                identifier = r["id"]
                other_cycles = r["cycles"]
                dest = other_results.get(identifier, [])
                dest.append(other_cycles)
                other_results[identifier] = dest

        for identifier, sim_cycles_list in other_results.items():
            if args.identifier is not None and identifier != args.identifier:
                continue

            rel_errors = []

            for ref, sim in zip(ref_cycles_list, sim_cycles_list):
                rel_error = abs(sim - ref) / ref
                rel_errors.append(rel_error)
            am_error = mean(rel_errors)

            exps = []
            for e in elist:
                ref_cycles = e.get_cycles()
                for r in e.other_results:
                    if r["id"] != identifier:
                        continue
                    sim_cycles = r["cycles"]
                    rel_error = abs(sim_cycles - ref_cycles) / ref_cycles
                    exps.append((rel_error, e, sim_cycles))

            acc_results.append((exp_len, 100 * am_error, identifier))


    configure_plot((6.8, 4.0))
    pd_data = pd.DataFrame(data=acc_results, columns=["exp_len", "val", "identifier"])

    axes = sns.pointplot(x="exp_len", y="val", data=pd_data, hue="identifier", markers=["o", "x"])

    xmax = max(x[0] for x in acc_results) + 1
    plt.ylim(0.0, max(x[1] for x in acc_results) * 1.1)
    axes.set(xlabel='length of experiments', ylabel="MAPE (%)")
    legend = axes.get_legend()
    legend.set_title("")

    if args.report is not None:
        dest_dir = os.path.dirname(args.report)
        dest_dir = os.path.abspath(dest_dir)
        filename = "varying_length.png"
        dest_file = pu.make_unique(os.path.join(dest_dir, filename))
        plt.savefig(dest_file)
        image_entry = {
                "kind": "image",
                "path": dest_file,
            }

        creation_date = datetime.datetime.now()
        cdate_str = creation_date.strftime('%Y-%m-%dT%H:%M:%S.%f')
        full_entry = {
                "category": "Evaluation of Measurements and Throughput Model",
                "caption": "MAPE of Predictions wrt. Measurements on SKL",
                "creation_date": cdate_str,
                "content": [image_entry],
            }
        report = [full_entry]
        report_file = pu.make_unique(args.report)
        with open(report_file, "w") as outfile:
            json.dump(report, outfile, indent=2, separators=(",", ": "))

if __name__ == "__main__":
    main()
