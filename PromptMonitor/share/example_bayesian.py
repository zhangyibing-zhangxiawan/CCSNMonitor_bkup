#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

from astropy import stats
import ROOT
import uproot as up
import matplotlib.pyplot as plt
plt.style.use('HXStyle')

infilename = '/junofs/users/huangx/myProject/CCSNMonitor/PromptMonitor/myJob/result/sn_intp3003.data/1/50/BayesianBlock/ncp9.3/promptTrigger_1.root'

def genRandomBkg(rate=1, N=None):
    rtime = []
    endTime = 100
    startTime = -100
    print('generating backgrounds..')
    bkgRate=rate #0.002 #unit: Hz
    if N is None:
        N=int(bkgRate*(endTime-startTime))
    rtime.append(startTime)
    #genrate random dt
    import random
    for ith in range(0, N):
        dt=random.expovariate(bkgRate)
        nextT=rtime[-1]+dt
        rtime.append(nextT)
    rtime.sort()
    return rtime

snTime = genRandomBkg()
with up.open(infilename) as infile:
    evttree = infile['tevt']
    readin = evttree.arrays(library='np')
    totEvts = len(readin['evtType'])
    for ith in range(0, totEvts):
        evttype = readin['evtType'][ith]
        evttime = readin['time'][ith]
        if evttype!=0: continue
        snTime.append(evttime)

snTime.sort()

timeEdge=list(stats.bayesian_blocks(snTime, ncp_prior=9.3))

fig, ax = plt.subplots()
ax.hist(snTime, bins=200, range=[timeEdge[0], timeEdge[-1]], histtype='step', density=True, label='equal bining')
ax.hist(snTime, bins=timeEdge, histtype='step', density=True, label='bayesian-block')
ax.legend()

ax.set(xlabel='t [s]', ylabel='rate [Hz]', yscale='log', title='Example of bayesian block method')

plt.show()
print(snTime)
