#!/usr/bin/python3
# -*- coding: utf-8 -*-
# author: Michal Knapik, ICS PAS 2014


import numpy as np


class simpleplanningdomain:
    """The domain for linear planning."""

    def __init__(self, typelist, initvec, finalvec, actions):
        self.typelist = typelist
        self.initvec = initvec
        self.finalvec = finalvec
        self.actions = actions        
        self.recomputevmax()
        self.initcopy = None

        #some redundancy here
        self.actNameToAction = {}
        for a in self.actions:
            self.actNameToAction[a[0]] = a
        self.actnames = self.actNameToAction.keys()

        #access only after running getHsequence
        self.kmax = None
        self.kgoal = None
        self.hsequence = None #fireable actions
        self.usequence = None #useless actions

    def getAction(self, actName):
        return self.actNameToAction[actName]

    def moveToOrigin(self):
        if self.initcopy is None:
            self.initcopy = np.copy(self.initvec)
            self.initvec -= self.initcopy
            self.finalvec -= self.initcopy

            for act in self.actions:
                act[1] -= self.initcopy
            self.recomputevmax()

    def restoreOrigin(self):
        if self.initcopy is not None:
            self.initvec, self.initcopy = self.initcopy, None
            self.finalvec += self.initvec

            for act in self.actions:
                act[1] += self.initvec
            self.recomputevmax()

    def recomputevmax(self):
        self.vmax = max(max([max(i[1]) for i in self.actions]), max(self.initvec), max(self.finalvec))

    def getEnabledActs(self, wrld, actset):
        enacts = []

        for act in actset:
            if min(wrld >= act[1]):
                enacts.append(act)

        return enacts
    
    def getHsequence(self):
        """Builds the H-sequence."""

        self.moveToOrigin()

        usefulActs = []
        rest = []

        #actions enabled by the initial world
        curr = self.getEnabledActs(self.initvec, self.actions)
        rest = self.actions[:]
        usefulActs.append(curr)
        greedyfire = 0
        self.kgoal, depth, foundkgoal = float('inf'), 0, False

        if min(self.initvec >= self.finalvec):
            self.kgoal, foundkgoal = -1, True

        while True:
            rest = [a for a in rest if a not in curr]
            #fire all actions from already enabled (curr and earlier)
            greedyfire += self.vmax * sum([act[2] for act in curr])

            if min(greedyfire >= self.finalvec) and not foundkgoal:
                self.kgoal, foundkgoal = depth, True
            else:
                depth += 1

            curr = self.getEnabledActs(greedyfire, rest)

            if len(curr) == 0:
                break

            usefulActs.append(curr)
        
        self.kmax = len(usefulActs) - 1
        self.restoreOrigin()

        self.hsequence = usefulActs
        self.usequence = rest

    def reportSequence(self):

        #build and display H-sequence
        print("H - sequence:")
        self.getHsequence()
        hsequence = self.hsequence
        usequence = self.usequence

        ctr = 0
        if self.kgoal < 0:
            print("(alert: the initial state enables the final one)")

        for s in self.hsequence:
            print("-(H" + str(ctr) + ")-")
            for a in s:
                print(a[0])
            ctr += 1
        print("(kgoal = {}, kmax = {})".format(self.kgoal, ctr - 1))

        #useless actions U
        print('-' * 45 + "\nUseless actions:")
        self.displayacts(self.usequence)

        if self.kgoal < float('inf'):
            #redundant actions R and possibly useful T
            print('-' * 45 + "\nRedundant, but not useless actions:")    
            nongreedyacts = sum(self.hsequence[self.kgoal + 1:], [])
            rnul, terrainc = [], []
    
            for act in nongreedyacts:

                if min(self.finalvec <= act[1]):
                    rnul.append(act)
                else:
                    terrainc.append(act)

            self.displayacts(rnul)

            print('-' * 45 + "\nNon-redundant, non-useless actions:")    
            self.displayacts(terrainc)
    
    def __str__(self):
        return """A planning domain with:
-initial world:
 {0}
-final world:
 {1}
-{2} types:
 {3}
-{4} actions:
{5}""".format(list(self.initvec), list(self.finalvec), len(self.typelist), ",".join(self.typelist), \
              len(self.actions), "\n".join([simpleplanningdomain.actiondesc(a) for a in self.actions]))
    
    @classmethod
    def actiondesc(cls, act):
        return " act: {0}\n pre: {1}\n eff: {2}".format(act[0], list(act[1]), list(act[2]))

    @classmethod
    def displayacts(cls, acts):
        if len(acts) == 0:
            print("none found")
        else:
            for a in acts:
                print(a[0])

