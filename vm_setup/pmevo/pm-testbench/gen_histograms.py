#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

import argparse
import datetime
import json
import os
from utils.experiment import ExperimentList

import seaborn as sns

import matplotlib as mpl
import matplotlib.pyplot as plt

from numpy import mean
from scipy.stats import pearsonr, spearmanr

from collections import defaultdict

import utils.plot_utils as pu

def configure_plot(size=None):
    if size is not None:
        plt.figure(figsize=size)
    sns.set(style="whitegrid")
    paper_rc = {'lines.linewidth': 0.1,
            'axes.edgecolor': 1.0,
            }
    sns.set_context('paper', rc=paper_rc)

def hist2d(identifier, meas, pred, title=None):
    size = 6.0
    configure_plot()
    # lim = 200
    lim = 35
    fig, ax = plt.subplots(figsize=(int(size*1.3),size), subplot_kw={ "aspect": "equal" })
    if title is None:
        fig.suptitle("prediction quality of '{}'".format(identifier.replace("_", "\\_")))
    elif title == "blank":
        pass
    else:
        fig.suptitle(title)
    ax.plot([0, lim], [0, lim], linewidth=0.8, color="g", rasterized=False)
    h, xedges, yedges, im = ax.hist2d(meas, pred, bins=lim, range=((0,lim), (0, lim)), cmap="binary", norm=mpl.colors.LogNorm(), rasterized=False)
    ax.set_xlabel('measured')
    ax.set_ylabel('predicted')
    ax.xaxis.set_ticks(range(0, lim+1, 5))
    ax.yaxis.set_ticks(range(0, lim+1, 5))
    cb = fig.colorbar(im)
    cb.ax.tick_params(which="both", width = 0.4)


def main():
    default_report = os.path.expanduser("~/reports/accuracy_report.json")
    argparser = argparse.ArgumentParser(description='Crunch the other_result entries of an experiment lists for statistics and plots')

    argparser.add_argument('exps', metavar='FILE', nargs='+', help='input experiment list(s) in json format')
    argparser.add_argument('-x', '--identifier', metavar="ID", default=None, help='only consider other_results with this identifier')

    argparser.add_argument('-p', '--plot', metavar='FILE', default=None, help='plot the results in the given file (use \'show\' for directly displaying the plot instead)')

    argparser.add_argument('-r', '--report', metavar='OUTFILE', default=default_report, help='name of a file to write a report file to (default: {})'.format(default_report))

    args = argparser.parse_args()

    report = []

    multiple_files = len(args.exps) > 1
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

        category = elist.arch.name

        for identifier, sim_cycles_list in other_results.items():
            if args.identifier is not None and identifier != args.identifier:
                continue
            print("statistics for '{}':".format(identifier))

            rel_errors = []

            for ref, sim in zip(ref_cycles_list, sim_cycles_list):
                rel_error = abs(sim - ref) / ref
                rel_errors.append(rel_error)
            am_error = mean(rel_errors)
            pearson_corr, p = pearsonr(ref_cycles_list, sim_cycles_list)
            spearman_corr, p = spearmanr(ref_cycles_list, sim_cycles_list)

            stats_str = ""
            stats_str += "  MAPE:        {:.2f}%\n".format(am_error * 100)
            stats_str += "  pearson CC:  {:.2f}\n".format(pearson_corr)
            stats_str += "  spearman CC: {:.2f}\n".format(spearman_corr)
            print(stats_str)

            if args.report is not None:
                table_entry = {
                        "kind": "table",
                        "rows": [
                                ["MAPE", "{:.2f}%".format(am_error * 100)],
                                ["Pearson CC", "{:.2f}".format(pearson_corr)],
                                ["Spearman CC", "{:.2f}".format(spearman_corr)],
                            ]
                    }

            exps = []
            for e in elist:
                ref_cycles = e.get_cycles()
                for r in e.other_results:
                    if r["id"] != identifier:
                        continue
                    sim_cycles = r["cycles"]
                    rel_error = abs(sim_cycles - ref_cycles) / ref_cycles
                    exps.append((rel_error, e, sim_cycles))

            if args.report is not None:
                dest_dir = os.path.dirname(args.report)
                dest_dir = os.path.abspath(dest_dir)
                filename = "heatmap_{}_{}.png".format(category, identifier)
                dest_file = pu.make_unique(os.path.join(dest_dir, filename))
                hist2d(identifier, meas=ref_cycles_list, pred=sim_cycles_list, title="blank")
                plt.savefig(dest_file)
                image_entry = {
                        "kind": "image",
                        "path": dest_file,
                    }

                creation_date = datetime.datetime.now()
                cdate_str = creation_date.strftime('%Y-%m-%dT%H:%M:%S.%f')
                full_entry = {
                        "category": "Evaluation Results for {}".format(category),
                        "caption": "Prediction Accuracy for {}".format(identifier),
                        "creation_date": cdate_str,
                        "content": [image_entry, table_entry],
                    }
                report.append(full_entry)

            if args.plot is not None:
                name = identifier
                if multiple_files:
                    name += " ({})".format(elist_file[-16:])
                hist2d(name, meas=ref_cycles_list, pred=sim_cycles_list, title=None)
                if args.plot != "show":
                    plt.savefig(args.plot)

    if args.report is not None:
        report_file = pu.make_unique(args.report)
        with open(report_file, "w") as outfile:
            json.dump(report, outfile, indent=2, separators=(",", ": "))

    if args.plot == "show":
        plt.show()

if __name__ == "__main__":
    main()
