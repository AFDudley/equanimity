import logilab.constraint as constraint
from logilab.constraint import *
from equanimity.const import ORTH, OPP, E, F, I, W
from copy import copy # tired.
need = {'E': 40, 'F':20, 'I': 10, 'W': 25}
silo = {'E': 30, 'F': 200, 'I': 0, 'W': 0}
print "given need: %s"%need
print "given silo: %s"%silo

#filter zeros
for k in need.keys():
    if need[k] < silo[k]:
        silo[k] -= need[k]
        need[k] = 0
    elif need[k] > silo[k]:
        need[k] -= silo[k]
        silo[k] = 0
    else:
        silo[k] = need[k] = 0
        
for k in need.keys():
    if need[k] == 0:
        del need[k]
    if silo[k] == 0:
        del silo[k]

print "current need: %s"%need
print "current silo: %s"%silo
varis = reduce(list.__add__, [[a + k for k, v in d.items() if v] for a, d in (('need', need), ('silo', silo))])
varis.sort()
constraints = []
vks = []
for n, v in enumerate(varis):
    if v[:4] == 'silo':
        for k in need.keys():
            vk = v + k
            vks.append(vk)

varis += vks
subs = {}
for n,v in enumerate(varis):
    if len(v) == 6:
        if v[-2] not in subs.keys():
            subs[v[-2]] = []
        subs[v[-2]].append(v)

for ele in subs.keys():
    sup = 'silo' + ele
    constraints.append(fd.make_expression((sup, ) + tuple(subs[ele]), "%s >= %s"%(sup,' + '.join(subs[ele]))))
 
for n, v in enumerate(varis):
    if v[:4] == 'need':
        # same element
        ele = 'silo' + v[-1] + v[-1]
        if ele in varis:
            new_vars =  [ele]
            str_thing = [ele]
        else:
            new_vars =  []
            str_thing = []
        # orth elements
        for n in ORTH[eval(v[-1])]:
            ele = 'silo' + n[0]  + v[-1]
            if ele in varis:
                new_vars.append(ele)
                str_thing += ['(' + ele  + '/2)']
        # opp elements
        opp = 'silo' + OPP[eval(v[-1])][0] + v[-1]
        if opp in varis:
            new_vars.append(opp)
            str_thing += ['(' + opp + '/4)']
        print "str_thing: %s"%str_thing
        constraints.append(fd.make_expression((v,), "%s == %s"%(v,need[v[-1]])))
        if len(str_thing) > 1:
            constraints.append(fd.make_expression((v, ) + tuple(new_vars), "%s == %s"%(v,' + '.join(str_thing))))
        elif len(str_thing) == 1:
            constraints.append(fd.make_expression((v, ) + tuple(new_vars), "%s == %s"%(v,str_thing[0])))

varis.sort()
#create domains
domains = {}
for n, v in enumerate(varis):
    if v[:4] == 'silo':
        if len(v) == 5: 
            rng = range(0, silo[v[-1]]+1)
        else:
            rng = range(0, silo[v[-2]]+1)
        domains[v]=fd.FiniteDomain(rng)
    else:
        domains[v]=fd.FiniteDomain(set([need[v[-1]],]))
        
r = Repository(varis,domains,constraints)
solutions = Solver().solve(r)
print solutions