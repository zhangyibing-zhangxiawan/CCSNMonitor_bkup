#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import numpy as np
def nIBD():
    topDir = '/junofs/users/huangx/myProject/CCSNMonitor/PromptMonitor/myJob/result/sn_gar81123/0/10/TimeInterval/2_T7.5'
    infilename = topDir + '/nevt.txt'
    a = np.loadtxt(infilename)
    meana = np.mean(a)
    print(a)
    print(meana)
    pass

if __name__ == '__main__':
    nIBD()
