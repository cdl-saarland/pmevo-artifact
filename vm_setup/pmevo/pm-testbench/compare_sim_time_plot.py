#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

import datetime
import os
import json
import argparse

import pandas as pd
import seaborn as sns

import matplotlib as mpl
import matplotlib.pyplot as plt

import utils.plot_utils as pu

def configure_plot(size):
    mpl.rcParams["pgf.rcfonts"] = False
    mpl.rcParams.update({'figure.autolayout': True})
    plt.figure(figsize=size)
    sns.set(style="whitegrid")
    paper_rc = {'lines.linewidth': 0.8,
            'axes.edgecolor': 1.0,
            }
    sns.set_context('paper', rc=paper_rc)

def main():
    default_report = os.path.expanduser("~/reports/sim_time_{}_report.json")
    argparser = argparse.ArgumentParser(description='Generate some plots')
    argparser.add_argument('infile', metavar='INFILE', help='the data in json format to crunch')
    argparser.add_argument('-o', '--out', metavar='OUTFILE', help='name of a file to write plot to')
    argparser.add_argument('-r', '--report', metavar='OUTFILE', default=None, help='name of a file to write a report file to (default: {})'.format(default_report.format("<explen|portnum>")))
    argparser.add_argument('-l', '--nologscale', action='store_true', help='do not use a log scale for printing')
    argparser.add_argument('--explen', action='store_true', help='test experiment length instead of port number')
    args = argparser.parse_args()

    configure_plot((6.8, 4.0))

    if args.explen:
        columns = ["num_insns", "num_ports", "num_insns_per_exp", "kind", "val"]
    else:
        columns = ["num_insns", "num_ports", "kind", "val"]
    arr = []

    with open(args.infile, 'r') as infile:
        indata = json.load(infile)
        # the first entry contains the used simulators
        simulators = indata[0]
        indata = indata[1:]
        kinds = list(simulators.keys())
        for d in indata:
            for kind in kinds:
                vals = []
                vals.append(d["arch_info"]["num_insns"])
                vals.append(int(d["arch_info"]["num_ports"]))
                if args.explen:
                    vals.append(int(d["num_insns_per_exp"]))
                vals.append(kind)
                vals.append(d["measured_secs_per_exp"][kind])
                arr.append(vals)

    index = list(range(len(arr)))

    pd_data = pd.DataFrame(data=arr, index=index, columns=columns)

    if args.explen:
        x_data = "num_insns_per_exp"
    else:
        x_data = "num_ports"

    axes = sns.pointplot(x=x_data, y="val", hue="kind", markers=["o", "x", "+"], data=pd_data)
    if args.explen:
        axes.set(xlabel='length of experiments', ylabel='time/experiment (s)')
    else:
        axes.set(xlabel='number of ports', ylabel='time/experiment (s)')
    if not args.nologscale:
        axes.set_yscale('log')

    legend = axes.get_legend()
    legend.set_title("")
    for x, k in enumerate(kinds):
        legend.texts[x].set_text(k)

    if args.report is None:
        report_file = default_report.format("explen" if args.explen else "portnum")
    else:
        report_file = args.report

    report_file = pu.make_unique(report_file)

    dest_dir = os.path.dirname(report_file)
    dest_dir = os.path.abspath(dest_dir)
    if args.explen:
        filename = "cmp_explen.png"
    else:
        filename = "cmp_portnum.png"
    dest_file = pu.make_unique(os.path.join(dest_dir, filename))
    plt.savefig(dest_file)
    image_entry = {
        "kind": "image",
        "path": dest_file,
    }

    if args.explen:
        caption = "Results with varying experiment length"
    else:
        caption = "Results with varying number of ports"
    creation_date = datetime.datetime.now()
    cdate_str = creation_date.strftime('%Y-%m-%dT%H:%M:%S.%f')
    full_entry = {
            "category": "Evaluation of the Bottleneck Simulation Algorithm",
            "caption": caption,
            "creation_date": cdate_str,
            "content": [image_entry],
        }
    report = [full_entry]
    with open(report_file, "w") as outfile:
        json.dump(report, outfile, indent=2, separators=(",", ": "))

    if args.out is not None:
        plt.savefig(args.out)
    # plt.show()

if __name__ == "__main__":
    main()
