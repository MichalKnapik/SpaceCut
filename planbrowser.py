#!/usr/bin/python2
# -*- coding: utf-8 -*-
# author: Michal Knapik, ICS PAS 2014

#all this is for debugging purposes only

from __future__ import print_function

import sys
import argparse
import functools
from z3 import *
from z3pyutilunbroken import *

def printPlan(mdl, allv):

    trueacts = [str(d) for d in mdl if is_true(mdl[d])]
    falseacts = [str(d) for d in mdl if is_false(mdl[d])]
    knownacts = trueacts + falseacts
    dncacts = [str(a) for a in allv if str(a) not in knownacts]

    nonplanacts = [a for a in trueacts + dncacts]
    print("{{ {} }}".format(", ".join(nonplanacts)))


if __name__ == "__main__":
    print("{:^45}".format("*** PlanBrowser ***"))
    print('-'*45)

    optpar = argparse.ArgumentParser(description="""SMT (non) plan browser for SpaceCut. 
    For now, it simply prints out a cover of non-plans actions.""")
    optpar.add_argument('file', metavar='file', type=str, help='input file')
    optpar.add_argument('maxp', metavar='maxPlans', type=int, help='maximal number of plans (default unbounded)', nargs='?')
    optpar.add_argument("-m", "--simpForm", help='print simplified formula', action="store_true")
                    
    args = optpar.parse_args()

    try:
        print("Reading {}".format(args.file))
        form = simplify(parse_smt2_file(args.file))
        maxp = args.maxp if args.maxp != None else float('inf')

        slv = Solver()
        slv.add(form)

        allvars = get_vars(form)

        if args.simpForm:
            print('simplified formula:')
            print(form)

        andl = lambda x, y: "(and {} {})".format(x, y)

        ctr = 0
        print('Non-plans are subsets of:')
        while slv.check() == sat and ctr < maxp:
            ctr += 1
            model = slv.model()
            print("{})".format(ctr), end = " ")
            printPlan(model, allvars)

            res = []
            meindecls = {}
            for d in model.decls():
                meindecls[str(d)] = d
                if is_true(model[d]):
                    res.append(str(d))
                else:
                    res.append("(not {})".format(str(d)))
            
            reduced = "(assert ( not {}))".format(functools.reduce(andl, res))
            notclause = parse_smt2_string(reduced, decls = meindecls)
            slv.add(notclause)

    except:
        print("*SMT formula reading error")
        raise
