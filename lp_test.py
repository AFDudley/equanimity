import logilab.constraint as lc
from equanimity.const import ORTH, OPP, E, F, I, W, ELEMENTS
from copy import copy # tired.

class LP_Solver(object):
    def __init__(self, silo, need):
        self.silo = silo
        self.need = need
        self.key = tuple([n[0] for n in ELEMENTS])
        self.prepare_comps()
        self.subs = {} #sub variables
        self.variables = self.generate_variables()
        self.constraints = self.generate_constraints()
        self.domains = self.generate_domains()
        self.solution = None
    
    def prepare_comps(self):
        """Does simple subtraction and removes zeroed keys to make generating 
        solver easier"""
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
        variables = reduce(list.__add__, [ \
        [a + k for k, v in d.items() if v] for a, d in (('need', self.need), 
                                                        ('silo', self.silo))])
        #self.variables.sort()
        
        # Create siloNM variables
        vks = []
        varis = copy(variables)
        for n, v in enumerate(varis):
            if v[:4] == 'silo':
                for k in self.need.keys():
                    vk = v + k
                    vks.append(vk)
        
        # place siloMN variables into self.subs
        varis += vks
        for n,v in enumerate(varis):
            if len(v) == 6:
                if v[-2] not in self.subs.keys():
                    self.subs[v[-2]] = []
                self.subs[v[-2]].append(v)
        variables = varis
        return variables
    
    def generate_constraints(self):
        """generate constraints used in the solver"""
        # Create siloN >= siloNM and siloN == silo[N] constraints
        constraints = []
        for ele in self.subs.keys():
            sup = 'silo' + ele
            constraints.append(lc.fd.make_expression((sup,),
            "%s == %s"%(sup,self.silo[ele[-1]])))
            constraints.append(lc.fd.make_expression((sup, ) +
            tuple(self.subs[ele]), "%s >= %s"%(sup,' + '.join(self.subs[ele]))))
        
        # Create needN constraints
        for n, v in enumerate(self.variables):
            if v[:4] == 'need':
                # same element
                ele = 'silo' + v[-1] + v[-1]
                if ele in self.variables:
                    new_vars =  [ele]
                    str_thing = [ele]
                else:
                    new_vars =  []
                    str_thing = []
                # orth elements
                for n in ORTH[eval(v[-1])]:
                    ele = 'silo' + n[0]  + v[-1]
                    if ele in self.variables:
                        new_vars.append(ele)
                        str_thing += ['(' + ele  + '/2)']
                # opp elements
                opp = 'silo' + OPP[eval(v[-1])][0] + v[-1]
                if opp in self.variables:
                    new_vars.append(opp)
                    str_thing += ['(' + opp + '/4)']
                # Create needN == self.need[N] constraint
                constraints.append(lc.fd.make_expression((v,),
                "%s == %s"%(v,self.need[v[-1]])))
                # Create needN == siloQN + siloXN + siloYN + siloZN constraint
                if len(str_thing) > 1:
                    constraints.append(lc.fd.make_expression((v, ) +
                    tuple(new_vars), "%s == %s"%(v,' + '.join(str_thing))))
                elif len(str_thing) == 1:
                    constraints.append(lc.fd.make_expression((v, ) +
                    tuple(new_vars), "%s == %s"%(v,str_thing[0])))
        #wee bit of optimization.
        constraints.sort(key = lambda c: len(c.formula), reverse=True)
        return constraints
        
    def generate_domains(self):
        """create domains"""
        domains = {}
        for n, v in enumerate(self.variables):
            if v[:4] == 'silo':
                if len(v) == 5: 
                    m = -1
                    #rng = range(0, silo[v[-1]]+1)
                else:
                    m = -2
                    #rng = range(0, silo[v[-2]]+1)
                #self.domains[v] = lc.fd.FiniteDomain(rng)
                domains[v] = lc.fd.FiniteDomain(range(0, self.silo[v[m]]+1))
            else:
                domains[v] = lc.fd.FiniteDomain(set([self.need[v[-1]],]))
        return domains
    def solve(self):
        r = lc.Repository(self.variables, self.domains, self.constraints)
        self.solution = lc.Solver().solve_one(r, verbose=0)
        #self.solution = lc.Solver().solve(r, verbose=1)

silo = {'E': 255, 'F': 0, 'I': 0, 'W': 255}
need = {'E': 0, 'F':60, 'I': 60, 'W': 0}
print "given silo: %s"%silo
print "given need: %s"%need
LP = LP_Solver(silo, need)
print "filtered silo: %s"%LP.silo
print "filtered need: %s"%LP.need
LP.solve()

print LP.solution
