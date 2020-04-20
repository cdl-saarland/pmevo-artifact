#! /usr/bin/env python3
# vim: et:ts=4:sw=4:fenc=utf-8

import argparse
from jsonable import Vault

def main():
    argparser = argparse.ArgumentParser(description='Script for finalizing progress files')
    argparser.add_argument('infile', metavar='INFILE', help='the progress file in json format to finalize')
    argparser.add_argument('-d', '--delete-progress', dest="delete_progress", action='store_true', help='delete the progress file after finalization')
    args = argparser.parse_args()

    vault = Vault(progressfile=args.infile)

    num = len(vault.model)

    vault.finalize(delete_progress=args.delete_progress)

    print("Written finalized result with {} entries into '{}'".format(num, vault.outfilename))



if __name__ == "__main__":
    main()
