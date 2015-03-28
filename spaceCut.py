#!/usr/bin/python3
# -*- coding: utf-8 -*-
# author: Michal Knapik, ICS PAS 2015

from parser import simpleparser
from checker import checker
import argparse
import time
import sys

class mytimr:
    """Rudimentary, measures real, not process time."""

    def start(self):
        self.timeNow = time.time()
    
    def timeRep(self):
        print("({0:.4f} sec.)".format(time.time() - self.timeNow))

if __name__ == "__main__":
    print("{:^45}".format("*** SpaceCut pruning tool ***"))
    print('-'*45)

    optpar = argparse.ArgumentParser(description='Monotone linear action space pruning tool.')
    optpar.add_argument('file', metavar='file', type=str, help='input file')
    optpar.add_argument('SATfile', metavar='SATfile', type=str, help='SAT output file')
    optpar.add_argument('depth', metavar='unwdepth', type=int, help='depth of unfolding', nargs='?')
    optpar.add_argument('dotfile', metavar='dotfile', type=str, help='dot file to save output', nargs='?')

    args = optpar.parse_args()
    prs = simpleparser.parser()

    tt = mytimr()
    tt.start()
    pd = prs.loadFile(args.file)
    tt.timeRep()

    print("\n{:^45}".format("--- Computing H - sequence ---"))
    tt.start()
    pd.reportSequence()
    tt.timeRep()

    dpth = float("inf") if args.depth == None else args.depth

    print("\n{:^45}\n{:^45}".format("--- Building full tree of non-plans ---", \
                                    "--- (with useless actions removed) ---"))
    tt.start()
    check = checker.oracle(pd)
    initnode = check.buildNonPlans(dpth)
    tt.timeRep()

    if args.dotfile != None:
        print("\n{:^45}".format("--- Saving tree ---"))
        tt.start()
        check.dumpNonPlansInDot(args.dotfile)
        tt.timeRep()
        print("Saved in {0}. To convert to pdf use: \ndot {0} -Tpdf -o {0}.pdf".format(args.dotfile))

    print("\n{:^45}".format("--- Saving SAT formula ---"))
    tt.start()
    satf = open(args.SATfile, 'w')
    satf.write(check.getActionSMTdefns(initnode))
    satf.write("\n(assert ")
    satf.write(check.dumpNonPlansInSAT(initnode))
    satf.write(")")
    tt.timeRep()
    print("Saved in {0}.".format(args.SATfile))

    print("\nAll done.")


