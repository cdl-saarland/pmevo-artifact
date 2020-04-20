#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

from utils.argparse_helper import add_server_args, add_bool_arg
from PITE.eval_server import start
import os
import sys
from shutil import which


def main():
    """
    This is the entrance of the PITE server.
    """
    import argparse
    argparser = argparse.ArgumentParser(description='Portable Instruction-Throughput Estimation Server')
    add_server_args(argparser)
    argparser.add_argument('--isa', metavar='ARCH', default=None,
                           help='the instruction set architecture this server is executed on')
    argparser.add_argument('--core', metavar='CORE', type=int, default="5",
                           help='the core on which the experiments shall be executed')
    argparser.add_argument('-n', '--numports', metavar='N', type=int, required=True,
                           help='the number of ports of the tested microarchitecture')
    argparser.add_argument('--iaca', action="store_true",
                           help='set everything up to use iaca instead of actual runs')
    argparser.add_argument('--noroot', action="store_true",
                           help='mute root warning')
    argparser.add_argument('--ithemal', action="store_true",
                           help='set everything up to use ithemal instead of actual runs (needs to be run inside ithemal docker image)')
    add_bool_arg(argparser, 'precise', 'Determine the loop body length in a more precise way. Might take a while!')
    add_bool_arg(argparser, 'newSU', 'redo the initial determination of the loop body length')
    args = argparser.parse_args()

    if os.geteuid() != 0 and not (args.iaca or args.ithemal or args.noroot):
        print("The PITE server requires root privileges for setting and accessing cpu frequency information!\n",
                "Please restart appropriately.",
                file=sys.stderr
            )
        sys.exit(1)

    if which("taskset") is None:
        print("Warning: The taskset command is not available, therefore experiment execution cannot be pinned to a specific core.", file=sys.stderr)

    start(args)


if __name__ == "__main__":
    main()
