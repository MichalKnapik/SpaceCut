#!/usr/bin/python3
# -*- coding: utf-8 -*-
# author: Michal Knapik, ICS PAS 2014


from plandomains import planningdomain
import numpy as np
import itertools
import functools
import sys


class node:

    #static
    nodecount = 0

    def __init__(self, acts, target, pldom):
        self.acts = list(acts)
        self.target = target
        self.pldom = pldom
        self.successors = None

        self.myhash = hash((str(self.acts), str(self.target)))
        self.myid = node.nodecount
        node.nodecount += 1

    def expand(self):
        """To be implemented in derived classes. 
        Returns a set of subnodes that are to be 
        connected below the node (successors)."""
        pass

    def traverse(self):
        """For debugging, mostly."""

        while True:
            suclist = self.getSuccessorsList()
            print(self)
            if(len(suclist) == 0):
                print("Terminal node, going up, press ENTER")
                input()
                return
            else:
                for i in range(len(suclist)):
                    print("[{}]: ".format(i) + str(suclist[i]))
                print("Select [-1 to move up, q to quit]: ", end = "", flush = True)
            ans = input()
            if(ans == 'q'):
                sys.exit()
            ans = int(ans)
            if ans == -1:
                return
            suclist[ans].traverse()
            
    def __str__(self):
        return """node no. {} with acts: {} \nand target: {}""".format(self.myid, self.acts, self.target)

    def __hash__(self):
        return self.myhash

    def __eq__(self, other):
        return self.acts == other.acts and min(self.target == other.target)

        
class join(node):

    def __init__(self, acts, target, pldom):
        node.__init__(self, acts, target, pldom)
        self.successors = []

    def expand(self):
        #process node
        for i in range(len(self.target)):
            if self.target[i] > 0:

                #i-th unitary vector
                ithunit = np.array([0] * i + [1] + [0]*(len(self.target) - i - 1))

                #build a new meet node
                mcand = meet(self.acts, ithunit, self.pldom)
                self.successors.append(mcand)

        return self.getSuccessorsList()

    def getSuccessorsList(self):
        return list(self.successors)

    def __str__(self):
        return "join " + node.__str__(self) + " and successors: (" + \
            " ".join([str(n.myid) for n in self.successors]) + ")" 

class meet(node):

    def __init__(self, acts, target, pldom):
        node.__init__(self, acts, target, pldom)
        self.successors = {} #act -> successor

    def __str__(self):
        return "meet " + node.__str__(self)  + " and successors: (" + \
            " ".join(["--{}--> {}".format(a, self.successors[a].myid) for a in self.successors]) + ")"

    def expand(self):
        #process node
        for pos in range(len(self.acts)):
            act = self.acts[pos]
            effact = self.pldom.getAction(act)[2]
            preact = self.pldom.getAction(act)[1]

            #test if the effect covers the target
            if min(effact >= self.target):
                reducedActs = self.acts[:pos] + self.acts[pos + 1:]
                
                #make a new join node
                mcjoin = join(reducedActs, preact, self.pldom)
                self.successors[act] = mcjoin
                
        return self.getSuccessorsList()

    def getSuccessorsList(self):
        return list(self.successors.values())

class oracle:
    
    def __init__(self, pldom):
        self.pldom = pldom
        self.initn = None #the initial node of non-plans

    def buildNonPlans(self, depth):
        #uses only non-useless actions!
        if self.pldom.kmax == None:
            print("Non-plans: building H - sequence")
            self.pldom.getHsequence()

        self.pldom.moveToOrigin()

        usefulactions = [a[0] for a in sum(self.pldom.hsequence, [])]
        self.initn = join(usefulactions, self.pldom.finalvec, self.pldom)
        frontier = set()
        frontier.add(self.initn)

        repmsg = ""
        ctr = 0
        while frontier and ctr < depth:

            new_frontier = set()

            for n in frontier:
                new_frontier.update(set(n.expand()))
            frontier = new_frontier
            ctr += 1

            repmsg = "Frontier size: {}, nodes: {}".format(str(len(frontier)), node.nodecount)
            print("\b"*len(repmsg) + repmsg, end = "", flush = True)

        print("\nCreated. Made {} nodes.".format(node.nodecount))

        self.pldom.restoreOrigin()
        return self.initn

    def dumpNonPlansInDot(self, fname):
        #warning - contains a recursive function

        def nodeToDot(anode, dtf):
            msg = "node: {}\nacts: {}\ntrgt: {}".format(anode.myid, ", ".join(anode.acts), str(tuple(anode.target)))

            succmsg = ""
            
            if type(anode) is meet:
                shp = "box"
                for a in anode.successors:
                    succmsg += "\n{}->{} [label =\" {}\"]".format(anode.myid, anode.successors[a].myid, a)

            elif type(anode) is join:
                shp = "ellipse"
                for a in anode.successors:
                    succmsg += "\n{}->{}".format(anode.myid, a.myid)

            dtf.write("\n\n{} [label = \"{}\", shape = {}]".format(anode.myid, msg, shp))
            dtf.write(succmsg)

        def recursiveDumpCall(anode, dtf):
            nodeToDot(anode, dtf)
            suclist = anode.getSuccessorsList()            

            for n in suclist:
                recursiveDumpCall(n, dtf)

        dotf = open(fname, 'w')
        dotf.write("digraph {} {{".format(fname))
        recursiveDumpCall(self.initn, dotf)
        dotf.write("\n}\n")
        dotf.close()

    def dumpNonPlansInSAT(self, anode):
        """Returns the SAT-formula (in SMT-lib rpn form) that
        describes all the non-plans in the planning domain."""
        #warning - contains a recursive function
        firstNode = anode
        allActs = anode.acts

        #lambda - expressions for joining actions
        orl = lambda x, y: "(or {} {})".format(x, y)
        andl = lambda x, y: "(and {} {})".format(x, y)

        def getPowerset(actionsIn, actionsOut = allActs):
            #returns the power set of actionsIn, with the remaining
            #actions forbidden (those from actionsOut)

            actsDisjunct = ""
            if(len(actionsIn)) > 0:
                actsDisjunct = functools.reduce(orl, actionsIn)

            negatedNonActs = ["(not {})".format(a) for a in actionsOut if a not in actionsIn]
            negatedNonActsConjunct = "" #conjunction of the negated remaining actions
            if(len(negatedNonActs)) > 0:
                negatedNonActsConjunct = functools.reduce(andl, negatedNonActs)

            if len(actsDisjunct) == 0:
                return negatedNonActsConjunct
            elif len(negatedNonActsConjunct) == 0:
                return actsDisjunct
            else:
                return "(and {} {})".format(actsDisjunct, negatedNonActsConjunct)

        def recursiveNonPlansInSATCall(anode):

            retv = ""
            suclist = anode.getSuccessorsList()
            if len(suclist) == 0: 
            #case: a terminal node
                if type(anode) is meet:
                    #the power set of anode.acts is the solution here
                    return getPowerset(anode.acts)
                    
                elif type(anode) is join:
                    #the solution here is the empty set 
                    return "false"

                else:
                    print("Error in SAT building. Unknown node type")
                    sys.exit()

            if type(anode) is meet:
            #case: a non-terminal node (len(suclist) > 0)
                successorsCallResults = []
                for an in anode.successors.items():
                    offact = an[0]
                    targetNode = an[1]
                    noOffactPower = getPowerset(targetNode.acts, [offact])
                    offactOut = recursiveNonPlansInSATCall(targetNode)
                    offactIn = "(and {} {})".format(offact, offactOut)
                    successorsCallResults.append("(or {} {})".format(offactIn, noOffactPower))

                if len(successorsCallResults) == 1:
                    return successorsCallResults[0]
                else:
                    return functools.reduce(andl, successorsCallResults)

            elif type(anode) is join:
                if len(suclist) == 1:
                    return recursiveNonPlansInSATCall(suclist[0])
                else:
                    return functools.reduce(orl, [recursiveNonPlansInSATCall(n) for n in suclist])

        return recursiveNonPlansInSATCall(anode)

    def getActionSMTdefns(self, anode):
        actres = []
        for a in anode.acts:
            actres.append("(declare-fun {} () Bool)".format(a))
            
        return "\n".join(actres)
