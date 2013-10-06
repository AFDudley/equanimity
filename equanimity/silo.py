"""
silo.py

Created by AFD on 2013-03-06.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import transaction

from stone import Stone, Composition
from const import ELEMENTS, ORTH, OPP


class Silo(Stone):
    """A silo is a really big stone that returns stones when requested."""

    def __init__(self, limit=None):
        Stone.__init__(self)
        #the limit will be set to 1.5 times a years harvest.
        if limit is not None:
            self.set_limit(self, limit)

    def set_limit(self, limit):
        self.limit.update(limit)
        transaction.commit()

    def transmute(self, comp):
        have = Composition.create(self.comp)
        cost = Composition(value=0)
        need = Composition.create(comp)

        # Extract the cheapest cost elements first
        for k, v in need.items():
            taking = min(v, have[k])
            have[k] -= taking
            need[k] -= taking
            cost[k] += taking

        # Extract the orth elements second
        # We will subtract from both orth to bring them as equal as possible
        # Since there are only 2 pairs of orth elements, it is safe to do this
        for k, v in need.items():
            orth = ORTH[k]
            # Select the greater of 2 orths
            higher = orth[0]
            lower = orth[1]
            if have[orth[1]] > higher:
                higher = orth[1]
                lower = orth[0]
            # If the higher amount is in excess by an odd number, let it keep
            # the extra single.
            diff = have[higher] - have[lower]
            if diff % 2:
                diff -= 1
            # Reduce the higher amount
            taking = min(diff, 2 * v)
            cost[higher] += taking
            have[higher] -= taking
            need[k] -= taking / 2
            v -= taking / 2
            # Adjust both orths equally as needed and possible
            remaining = min(have[higher], have[lower])
            taking = min(remaining, v)
            have[higher] -= taking
            have[lower] -= taking
            cost[higher] += taking
            cost[lower] += taking
            need[k] -= taking

        # Extract the opp elements last
        for k, v in need.items():
            opp = OPP[k]
            taking = min(have[opp] / 4, v)
            need[k] -= taking
            have[opp] -= taking * 4

        # If we have any remaining needed value to reach the requested stone,
        # we failed
        if need.value():
            raise ValueError('Not enough to transmute')

        # Pay for it
        self.split(cost)
        return Stone(comp)


    #def transmute(self, comp):
        #"""attempts to transmute existing points into Stone of equested comp.
        #"""
        ##BROKEN. whoops this is an actual math problem.
        ##2 to 1 for orth elements
        ##4 to 1 for opp elements (which is the same as doing orth twice :)
        #negcomp = {"Earth": 0, "Fire": 0, "Ice": 0, "Wind": 0}
        #for element in ELEMENTS:
            #neg = self.comp[element] - comp[element]
            #if neg < 0:
                #negcomp[element] += neg
            #else:
                #del negcomp[element]
        #if len(negcomp):
            #for element in ELEMENTS:
                #neg = self.comp[element] - comp[element]
                #print "element: %s neg: %s" % (element, neg)
                #if neg < 0:
                    #cost = 2 * abs(neg)  # the abs is for clarity.
                    #orthsum = sum([self.comp[x] for x in ORTH[element]])
                    #remainder = orthsum - cost
                    #print ("element: {0} cost: {1} orthsum: {2} remainder: "
                           #"{3}").format(element, cost, orthsum, remainder)
                    #if remainder <= 0:  # then we take from OPP
                        #new_cost = 2 * abs(remainder)
                        #if new_cost > self.comp[OPP[element]]:
                            #raise Exception("There are not enough points to "
                                            #"complete the transmutation.")
                        #else:
                            #print "new cost %s" % new_cost
                            #self.comp[element] = 0
                            #self.comp[ORTH[element][0]] = 0
                            #self.comp[ORTH[element][1]] = 0
                            ##self.comp[OPP[element]] -= new_cost
                    #else:
                        #new_remainder = self.comp[ORTH[element][0]] - cost
                        #print "new_remainder: %s" % new_remainder
                        #if new_remainder > 0:
                            #self.comp[element] = 0
                            #self.comp[ORTH[element][0]] -= cost
                        #else:
                            #self.comp[element] = 0
                            #self.comp[ORTH[element][0]] = 0
                            #self.comp[ORTH[element][1]] -= new_remainder
                ##s = Stone()
                ##s.limit.update(comp)
                ##s.comp = comp #nasty hack for "Big" stones.
                #transaction.commit()
                #return Stone(comp)
        #else:
            #raise Exception("Do not call transmute directly, call get.")

    def get(self, comp):
        """Attempts to split the requsted stone,
        attempts transmuation if split fails."""
        comp = Composition.create(comp)
        if sum(comp.values()) > self.value():
            msg = ("There are not enough points in the silo to create a stone "
                   "of {0}")
            raise ValueError(msg.format(comp))
        else:
            return self.split(comp)

    def imbue_list(self, los):
        """surplus is destroyed."""
        for stone in los:
            self.imbue(stone)
