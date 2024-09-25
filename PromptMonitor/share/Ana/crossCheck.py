#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import os
class crossCheck():
    def __init__(self):
        self.topdir = '/junofs/users/huangx/myProject/CCSNMonitor/PromptMonitor/myJob/result/sn_gar82703/1/310/BayesianBlock/ncp9.1'
        self.timesig = {}
        self.nsig = {}

    def readTime(self, ith):
        infileName = self.topdir + '/promptTrigger_%d.root'%ith
        sigtime = []
        if not os.path.isfile(infileName):
            self.nsig[ith] = 0
            self.timesig[ith] = []
            return
        import uproot as up
        with up.open(infileName) as infile:
            #evtTree = infile['tevt']
            #readin = evtTree.arrays(library='np')
            #thetype = list(readin['evtType'])
            #thetime = list(readin['time'])
            #nevt = len(thetype)
            #for ii in range(0, nevt):
            #    if thetype[ii]==0:
            #        sigtime.append(thetime[ii])
            trigTree = infile['ttrig']
            readin = trigTree.arrays(library='np')
            lentrig = len(readin['snTriggerTime'])
            if lentrig>0:
                self.nsig[ith] = 1
            else:
                self.nsig[ith] = 0
        #self.nsig[ith] = len(sigtime)
        #self.timesig[ith] = sigtime

    def print(self):
        print(self.nsig)
        pass
    pass

if __name__ == '__main__':
    thecheck = crossCheck()
    for ii in range(0, 200):
        thecheck.readTime(ii)
    thecheck.print()
