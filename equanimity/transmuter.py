import logilab.constraint as lc
from equanimity.const import ORTH, OPP, ELEMENTS, LETTERS
from equanimity.stone import Stone, Composition


class Transmuter(object):
    """Takes a silo comp and need comp and returns the stone to be split
    from the silo or None."""

    def __init__(self, silo, need):
        self.silo = dict(silo)
        self.need = dict(need)
        # TODO -- if we want to cache answer, at this point we would lookup
        # a previous solution based on inputs
        self.solution = None
        self.failed = False

    def get_cost(self):
        """ Return the cost of transmuting 'need' from 'silo' as a Stone """
        # Check previous runs
        if self.failed:
            self._fail()
        if self.solution is not None:
            return Stone(self.solution)

        # Do simple accounting, check for answer without hitting solver
        silo, need = self._prepare_comps(self.silo, self.need)
        if not need:
            print silo, need
            print self.silo, self.need
            # Silo provided everything
            self.solution = self.need
            return Stone(self.need)
        elif not silo:
            # Silo has nothing left in it, be we still need something
            return self._fail()

        # Setup solver
        variables, subvariables = self._generate_variables(silo, need)
        constraints = self._generate_constraints(silo, need, variables,
                                                 subvariables)
        domains = self._generate_domains(silo, need, variables)
        solution = self._solve(variables, domains, constraints)
        self.solution = self._compute_cost(solution)
        return Stone(self.solution)

    def _filter_zeroes(self, comp):
        return {k: v for k, v in comp.iteritems() if v}

    def _prepare_comps(self, _silo, _need):
        """Does simple subtraction and removes zeroed keys to make"""
        """ generating solver easier"""
        silo = dict(_silo)
        need = dict(_need)
        for k in ELEMENTS:
            taking = min(_silo[k], _need[k])
            if taking < 0:
                msg = 'Invalid silo, need: {0}, {1}'
                raise ValueError(msg.format(_silo, _need))
            silo[k] -= taking
            need[k] -= taking
        return self._filter_zeroes(silo), self._filter_zeroes(need)

    def _generate_variables(self, silo, need):
        """generates the variables and subvariables used in the solver"""
        # Create needN and siloN variables.
        variables = ['silo' + k[0] for k in silo]
        variables += ['need' + k[0] for k in need]

        # Create siloNM variables
        for v in variables[:]:
            if v.startswith('silo'):
                for k in need:
                    vk = v + k[0]
                    variables.append(vk)

        # place siloMN variables into subvariables
        subvariables = {}
        for v in variables:
            if len(v) == 6:
                subvariables.setdefault(v[4:5], []).append(v)
        return variables, subvariables

    def _generate_constraints(self, silo, need, variables, subvariables):
        """generate constraints used in the solver"""
        # Create siloN >= siloNM and siloN == silo[N] constraints
        constraints = []
        for ele in subvariables:
            sup = 'silo' + ele[0]
            c = "%s == %s" % (sup, silo[LETTERS[ele[0]]])
            constraints.append(lc.fd.make_expression((sup,), c))
            args = (sup,) + tuple(subvariables[ele])
            c = "%s >= %s" % (sup, ' + '.join(subvariables[ele]))
            constraints.append(lc.fd.make_expression(args, c))

        # Create needN constraints
        for v in variables:
            if not v.startswith('need'):
                continue
            # same element
            ele = 'silo' + v[-1] + v[-1]
            if ele in variables:
                new_vars = [ele]
                str_thing = [ele]
            else:
                new_vars = []
                str_thing = []
            # orth elements
            for n in ORTH[LETTERS[v[-1]]]:
                ele = 'silo' + n[0] + v[-1]
                if ele in variables:
                    new_vars.append(ele)
                    str_thing += ['({0}/2)'.format(ele)]
            # opp elements
            opp = 'silo' + OPP[LETTERS[v[-1]]][0] + v[-1]
            if opp in variables:
                new_vars.append(opp)
                str_thing += ['({0}/4)'.format(opp)]
            # Create needN == need[N] constraint
            c = "%s == %s" % (v, need[LETTERS[v[-1]]])
            constraints.append(lc.fd.make_expression((v,), c))
            # Create needN == siloQN + siloXN + siloYN + siloZN constraint
            args = (v,) + tuple(new_vars)
            c = "%s == %s" % (v, ' + '.join(str_thing))
            constraints.append(lc.fd.make_expression(args, c))

        # wee bit of optimization.
        constraints.sort(key=lambda c: len(c.formula), reverse=True)
        return constraints

    def _generate_domains(self, silo, need, variables):
        """create domains"""
        domains = {}
        for v in variables:
            if v.startswith('silo'):
                if len(v) == 5:
                    m = silo[LETTERS[v[-1]]] + 1
                else:
                    m = silo[LETTERS[v[-2]]] + 1
                domains[v] = lc.fd.FiniteDomain(range(0, m))
            else:
                d = set([need[LETTERS[v[-1]]]])
                domains[v] = lc.fd.FiniteDomain(d)
        return domains

    def _fail(self):
        self.failed = True
        raise ValueError("Cannot transmute stones in silo to needed stone.")

    def _solve(self, variables, domains, constraints):
        r = lc.Repository(variables, domains, constraints)
        return lc.Solver().solve_one(r, verbose=0)

    def _compute_cost(self, solution):
        if solution is None:
            return self._fail()
        comp = Composition(0)
        for k, v in solution.iteritems():
            if len(k) == 6:
                comp[LETTERS[k[-2]]] += v
        for e in ELEMENTS:
            comp.setdefault(e, 0)
        return comp
