"""
silo.py

Created by AFD on 2013-03-06.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import transaction

from stone import Stone
from const import ELEMENTS, ORTH, OPP


class Silo(Stone):
    """A silo is a really big stone that returns stones when requested."""
    def set_limit(self, limit):
        self.limit.update(limit)
        self._p_changed = 1
        transaction.commit()

    def __init__(self, limit=None):
        Stone.__init__(self)
        #the limit will be set to 1.5 times a years harvest.
        if limit is not None:
            self.set_limit(self, limit)

    def transmute(self, comp):
        """attempts to transmute existing points into Stone of equested comp.
        """
        #BROKEN. whoops this is an actual math problem.
        #2 to 1 for orth elements
        #4 to 1 for opp elements (which is the same as doing orth twice :)
        negcomp = {"Earth": 0, "Fire": 0, "Ice": 0, "Wind": 0}
        for element in ELEMENTS:
            neg = self.comp[element] - comp[element]
            if neg < 0:
                negcomp[element] += neg
            else:
                del negcomp[element]
        if len(negcomp):
            for element in ELEMENTS:
                neg = self.comp[element] - comp[element]
                print "element: %s neg: %s" % (element, neg)
                if neg < 0:
                    cost = 2 * abs(neg)  # the abs is for clarity.
                    orthsum = sum([self.comp[x] for x in ORTH[element]])
                    remainder = orthsum - cost
                    print ("element: {0} cost: {1} orthsum: {2} remainder: "
                           "{3}").format(element, cost, orthsum, remainder)
                    if remainder <= 0:  # then we take from OPP
                        new_cost = 2 * abs(remainder)
                        if new_cost > self.comp[OPP[element]]:
                            raise Exception("There are not enough points to "
                                            "complete the transmutation.")
                        else:
                            print "new cost %s" % new_cost
                            self.comp[element] = 0
                            self.comp[ORTH[element][0]] = 0
                            self.comp[ORTH[element][1]] = 0
                            #self.comp[OPP[element]] -= new_cost
                    else:
                        new_remainder = self.comp[ORTH[element][0]] - cost
                        print "new_remainder: %s" % new_remainder
                        if new_remainder > 0:
                            self.comp[element] = 0
                            self.comp[ORTH[element][0]] -= cost
                        else:
                            self.comp[element] = 0
                            self.comp[ORTH[element][0]] = 0
                            self.comp[ORTH[element][1]] -= new_remainder
                #s = Stone()
                #s.limit.update(comp)
                #s.comp = comp #nasty hack for "Big" stones.
                self._p_changed = 1
                transaction.commit()
                return Stone(comp)
        else:
            raise Exception("Do not call transmute directly, call get.")

    def get(self, comp):
        """Attempts to split the requsted stone,
        attempts transmuation if split fails."""
        if sum(comp.values()) > self.value():
            msg = ("There are not enough points in the silo to create a stone "
                   "of {0}")
            raise ValueError(msg.format(comp))
        else:
            # these will fail if comp > limit
            try:
                s = self.split(comp)
                self._p_changed = 1
                transaction.commit()
                return s
            except:
                raise
                #raise Exception("Transmute not implemented.")
                """s = self.transmute(comp)
                return s"""

    def imbue_list(self, loS):
        """surplus is destroyed."""
        for stone in loS:
            self.imbue(stone)
