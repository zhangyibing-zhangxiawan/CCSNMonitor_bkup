#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import ROOT

def nIBD():
    topDir = '/junofs/users/huangx/myProject/CCSNMonitor/OnlineMonitor/OnlineMonitor/myJob'
    infileDir = '/result_SlidingWindow_36GW/sn_intp1311.data/1/10/SlidingWindow/sT10_fT1e-1_3/toybkg0'
    for ith in range(0, 200):
        infileName = infileDir + 'sn_%d.root'%ith
    pass

if __name__ == '__main__':
    nIBD()
