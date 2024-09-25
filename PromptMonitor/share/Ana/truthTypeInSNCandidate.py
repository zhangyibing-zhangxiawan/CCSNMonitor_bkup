#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin
# = Calculate the fraction of truth type in SN candidates =

import sys
import numpy as np
import uproot as up

class typeFraction():
    def __init__(self):
        self.type_truth = []
        self.type_sel = []
        pass

    def readTruthFile(self, ith):
        infileName = '/junofs/users/huangx/myProject/myJUNOCommon/evtTruth/myJob/result/sn_intp3003.data/0/dist10/sn_%dth.root'%ith
        with up.open(infileName) as infile:
            tree_evttruth = infile['evtTruth']
            readin = tree_evttruth.arrays(library='np')
            self.type_truth.extend(list(readin['evtType']))
        pass

    def readMonitorFile(self, ith):
        infileName = '/junofs/users/huangx/myProject/CCSNMonitor/PromptMonitor/myJob/result/sn_intp3003.data/0/10/TimeInterval/2_T2.1/promptTrigger_%d.root'%ith
        with up.open(infileName) as infile:
            tree_tevt = infile['tevt']
            readin = tree_tevt.arrays(library='np')
            self.type_sel.extend(list(readin['evtType']))
        pass

    def calculate(self):
        print(len(self.type_truth), len(self.type_sel))
        tot_snlike = 0
        tot_IBD = 0
        tot_other = 0
        for truthType, selType in zip(self.type_truth, self.type_sel):
            if selType!=0: continue
            tot_snlike += 1
            if truthType=='IBDp':
                tot_IBD += 1
            else:
                print(truthType, end=' ')
                tot_other += 1
        print(tot_snlike, tot_IBD, tot_other)
        print(tot_IBD/tot_snlike, tot_other/tot_snlike)
        pass
    pass

if __name__ == '__main__':
    typefracObj = typeFraction()
    for ii in range(0, 20):
        typefracObj.readTruthFile(ii)
        typefracObj.readMonitorFile(ii)
        break
    typefracObj.calculate()
