# -*- coding: utf-8 -*-
# author: Michal Knapik, ICS PAS 2015


import re
import numpy as np
from plandomains import planningdomain
import sys


class parser:
    """Loads an explicit simple planning domain."""

    def __init__(self):
        vectpatt = r'\s*\((.*)\)'
        self.typeslistre = re.compile(r'types\s*:\s*((\w*\s*,\s*)*\w*)')
        self.initstre = re.compile(r'initial:{}'.format(vectpatt))
        self.finstre = re.compile(r'final:{}'.format(vectpatt))
        self.transre = re.compile(r'name:\s*(\w*)\s*input:\s*{0}\s*output:{0}\s*'.format(vectpatt))

    def loadFile(self, filename):
        print('Reading from ' + filename + '\n' + '-'*45)

        try:        
            with open(filename, 'r') as fl:
                txt = fl.read()

                #fetch preamble
                typs = parser.fetchVector(self.typeslistre.search(txt).group(1))
                inits = parser.strVectToNpArray(parser.fetchVector(self.initstre.search(txt).group(1)))
                finst = parser.strVectToNpArray(parser.fetchVector(self.finstre.search(txt).group(1)))

                #fetch actions
                acts = [[act[0], parser.fetchNpArray(act[1]), parser.fetchNpArray(act[2])] for act in self.transre.findall(txt)]

                #for now, we don't allow nondeterminism
                actn = [act[0] for act in acts]
                for a in actn:
                    if actn.count(a) > 1:
                        print("Non-deterministic action {}. Quitting.".format(a))
                        sys.exit()

                return planningdomain.simpleplanningdomain(typs, inits, finst, acts)

        except (ValueError, IOError) as e:
            print("*Parsing error")
            raise

    @classmethod
    def fetchVector(cls, strn):
        return strn.replace(" ","").split(",")

    @classmethod
    def fetchNpArray(cls, strn):
        strvec = parser.fetchVector(strn)
        return parser.strVectToNpArray(strvec)

    @classmethod
    def strVectToNpArray(cls, stvec):
        return np.array([int(i) for i in stvec])

    
