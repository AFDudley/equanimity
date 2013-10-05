import logilab.constraint as constraint
from logilab.constraint import *
from equanimity.const import ORTH, OPP, E, F, I, W
T = {'E': 40, 'F': 40, 'I': 13, 'W': 2}
A = {'E': 20, 'F': 500, 'I': 2, 'W': 0}
#filter zeros
for k in T.keys():
    if T[k] == 0:
        del T[k]
    elif T[k] < A[k]:
        del T[k]
print "current T: %s"%T
print "current A: %s"%A
varis = reduce(list.__add__, [[a + k for k, v in d.items() if v] for a, d in (('T', T), ('A', A))])
varis.sort()
#create domains
domains = {}
for n, v in enumerate(varis):
    if v[0] == 'A':
        domains[v]=fd.FiniteDomain(range(0,A[v[1]]+1))
    else:
        domains[v]=fd.FiniteDomain(set([T[v[1]],]))

#create constraints
constraints = []
for n, v in enumerate(varis):
    if v[0] == 'A':
        constraints.append(fd.make_expression((v,), "%s >= 0"%v))
        constraints.append(fd.make_expression((v,), "%s <= %s"%(v,A[v[1]])))
    else:
        # same element
        ele = 'A' + v[1]
        if ele in varis:
            new_vars =  [ele]
            str_thing = [ele]
        else:
            new_vars =  []
            str_thing = []
        # orth elements
        for n in ORTH[eval(v[1])]:
            ele = 'A' + n[0]
            if ele in varis:
                new_vars.append(ele)
                str_thing += ['(' + ele  + '/2)']
        # opp elements
        opp = 'A' + OPP[eval(v[1])][0]
        if opp in varis:
            new_vars.append(opp)
            str_thing += ['(' + opp + '/4)']
        new_vars = ','.join(new_vars)
        constraints.append(fd.make_expression((v,), "%s == %s"%(v,T[v[1]])))
        constraints.append(fd.make_expression((v, ) + tuple(new_vars.split(',')), "%s == %s"%(v,' + '.join(str_thing))))
r = Repository(varis,domains,constraints)
solutions = Solver().solve(r)
print solutions