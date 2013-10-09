import logilab.constraint as lc
from equanimity.const import ORTH, OPP, E, F, I, W, ELEMENTS
from equanimity.stone import Stone
from copy import copy


class Transmuter(object):
    """takes a silo comp and need comp and returns the stone to be split """
    """from the silo or None."""
    def __init__(self, silo, need):
        E, F, I, W  # LOL.
        if sum(silo.values()) > 0:
            self.silo = dict(silo)
        else:
            raise ValueError("silo value must be greater than zero.")
        if sum(need.values()) > 0:
            self.need = dict(need)
        else:
            raise ValueError("need value must be greater than zero.")
        self.key = ELEMENTS
        self.prepare_comps()
        self.subs = {}  # sub variables
        self.variables = self.generate_variables()
        self.constraints = self.generate_constraints()
        self.domains = self.generate_domains()
        self.solution = None

    def prepare_comps(self):
        """Does simple subtraction and removes zeroed keys to make"""
        """ generating solver easier"""
        #Simple subtraction
        for k in self.key:
            if self.need[k] < self.silo[k]:
                self.silo[k] -= self.need[k]
                self.need[k] = 0
            elif self.need[k] > self.silo[k]:
                self.need[k] -= self.silo[k]
                self.silo[k] = 0
            else:
                self.silo[k] = self.need[k] = 0
        #Filter zeros
        for k in self.key:
            if self.need[k] == 0:
                del self.need[k]
            if self.silo[k] == 0:
                del self.silo[k]

    def generate_variables(self):
        """generates the variables and subs used in the solver"""
        # Create needN and siloN variables.
        variables = reduce(list.__add__, [
            [a + k[0] for k, v in d.items() if v] for a,
            d in (('need', self.need), ('silo', self.silo))])

        # Create siloNM variables
        vks = []
        varis = copy(variables)
        for n, v in enumerate(varis):
            if v[:4] == 'silo':
                for k in self.need.keys():
                    vk = v + k[0]
                    vks.append(vk)

        # place siloMN variables into self.subs
        varis += vks
        for n, v in enumerate(varis):
            if len(v) == 6:
                if v[4:5] not in self.subs.keys():
                    self.subs[v[4:5]] = []
                self.subs[v[4:5]].append(v)
        variables = varis
        return variables

    def generate_constraints(self):
        """generate constraints used in the solver"""
        # Create siloN >= siloNM and siloN == silo[N] constraints
        constraints = []
        for ele in self.subs.keys():
            sup = 'silo' + ele[0]
            constraints.append(lc.fd.make_expression((sup,),
                               "%s == %s" %
                               (sup, self.silo[eval(ele[0])])))
            constraints.append(lc.fd.make_expression((sup, ) +
                               tuple(self.subs[ele]),
                               "%s >= %s" %
                               (sup, ' + '.join(self.subs[ele]))))
        # Create needN constraints
        for n, v in enumerate(self.variables):
            if v[:4] == 'need':
                # same element
                ele = 'silo' + v[-1] + v[-1]
                if ele in self.variables:
                    new_vars = [ele]
                    str_thing = [ele]
                else:
                    new_vars = []
                    str_thing = []
                # orth elements
                for n in ORTH[eval(v[-1])]:
                    ele = 'silo' + n[0] + v[-1]
                    if ele in self.variables:
                        new_vars.append(ele)
                        str_thing += ['(' + ele + '/2)']
                # opp elements
                opp = 'silo' + OPP[eval(v[-1])] + v[-1]
                if opp in self.variables:
                    new_vars.append(opp)
                    str_thing += ['(' + opp + '/4)']
                # Create needN == self.need[N] constraint
                constraints.append(lc.fd.make_expression((v, ),
                                   "%s == %s" %
                                   (v, self.need[eval(v[-1])])))
                # Create needN == siloQN + siloXN + siloYN + siloZN constraint
                if len(str_thing) > 1:
                    constraints.append(lc.fd.make_expression((v, ) +
                                       tuple(new_vars),
                                       "%s == %s" %
                                       (v, ' + '.join(str_thing))))
                elif len(str_thing) == 1:
                    constraints.append(lc.fd.make_expression((v, ) +
                                       tuple(new_vars),
                                       "%s == %s" % (v, str_thing[0])))
        #wee bit of optimization.
        constraints.sort(key=lambda c: len(c.formula), reverse=True)
        return constraints

    def generate_domains(self):
        """create domains"""
        domains = {}
        for n, v in enumerate(self.variables):
            if v[:4] == 'silo':
                if len(v) == 5:
                    m = self.silo[eval(v[-1])]+1
                else:
                    m = self.silo[eval(v[-2])]+1
                domains[v] = lc.fd.FiniteDomain(range(0, m))
            else:
                domains[v] = lc.fd.FiniteDomain(set([
                    self.need[eval(v[-1])], ]))
        return domains

    def solve(self):
        r = lc.Repository(self.variables, self.domains, self.constraints)
        self.solution = lc.Solver().solve_one(r, verbose=0)

    def get_split(self):
        stone = Stone()
        self.solve()
        if self.solution is not None:
            for k in self.solution.keys():
                if len(k) != 6:
                    del self.solution[k]
            for k in self.solution.keys():
                stone[eval(k[-2])] += self.solution[k]
            return stone
        else:
            raise ValueError("Cannot transmute stones in silo to needed \
                            stone.")
