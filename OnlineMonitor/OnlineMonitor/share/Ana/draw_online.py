#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import onlineMonitor
import matplotlib.pyplot as plt
import sys

def eff_sn(method, far, saveFigs=False):
    if method not in ['SlidingWindow', 'TimeInterval', 'BayesianBlock']:
        print('Unknow alert method!')
        sys.exit()
    monitors = []
    for thisfar in far:
        par = None
        if method == 'SlidingWindow':
            par = onlineMonitor.par_slidingWindow('sn', thisfar)
        elif method == 'TimeInterval':
            par = onlineMonitor.par_timeInterval('sn', thisfar)
        else:
            par = onlineMonitor.par_bayesianBlock('sn', thisfar)
        themonitor = onlineMonitor.onlineMonitor()
        themonitor.setPar(par)
        #----------Read the data
        #for model in ['intp1311.data', 'intp3003.data']:
        for model in ['intp1311.data', 'intp3003.data', 'gar81123', 'gar82703']:
            for mo in [0, 1]:
                themonitor.readSNResultFromTxt(model, mo)
        themonitor.calEff(totN=1)
        monitors.append(themonitor)
    #----------Draw the plot
    thedrawing = onlineMonitor.onlineMonitor_draw()
    thedrawing.setMonitors(monitors)
    #curves = [('intp1311.data', 0), ('intp1311.data', 1), ('intp3003.data', 0), ('intp3003.data', 1)]
    curves = [('gar81123', 0), ('gar81123', 1), ('gar82703', 0), ('gar82703', 1)]
    #thedrawing.drawEffciency('online-sn_eff_%s_%s'%(method, far[0]), curves)
    thedrawing.drawEffciency_all('online-sn_eff_%s_%s'%(method, far[0]))

    if saveFigs:
        thedrawing.saveFigs()

    plt.show()
    pass

def cmpeff_sn(model, far, saveFigs=False):
    if model not in ['gar81123', 'gar82703', 'intp1311.data', 'intp3003.data']:
        print('Unknow SN model!')
        sys.exit()
    par = {}
    par['SlidingWindow'] = onlineMonitor.par_slidingWindow('sn', far)
    par['TimeInterval'] = onlineMonitor.par_timeInterval('sn', far)
    par['BayesianBlock'] = onlineMonitor.par_bayesianBlock('sn', far)
    monitors = []
    #----------Read the data
    for method in ['SlidingWindow', 'TimeInterval', 'BayesianBlock']:
        themonitor = onlineMonitor.onlineMonitor()
        themonitor.setPar(par[method])
        for mo in [0, 1]:
            themonitor.readSNResultFromTxt(model, mo)
        themonitor.calEff(totN=1)
        monitors.append(themonitor)
    #----------Draw the plot
    thedrawing = onlineMonitor.onlineMonitor_draw()
    thedrawing.setMonitors(monitors)
    thedrawing.drawEffciency_cmp('online-sn_eff_cmp_%s'%far, curves=[(model, 0), (model, 1)])

    if saveFigs:
        thedrawing.saveFigs()

    plt.show()
    pass

def effAndTime_presn(method, far, saveFigs=False):
    if method not in ['SlidingWindow', 'TimeInterval', 'BayesianBlock']:
        print('Unknow alert method!')
        sys.exit()
    monitors = []
    for thisfar in far:
        par = None
        if method == 'SlidingWindow':
            par = onlineMonitor.par_slidingWindow('presn', thisfar)
        elif method == 'TimeInterval':
            par = onlineMonitor.par_timeInterval('presn', thisfar)
        else:
            par = onlineMonitor.par_bayesianBlock('presn', thisfar)
        themonitor = onlineMonitor.onlineMonitor()
        themonitor.setPar(par)
        #----------Read the data
        for model in ['prePatton15', 'prePatton30']:
            for mo in [0, 1]:
                themonitor.readpreSNResultFromTxt(model, mo)
        themonitor.calEff()
        themonitor.calTime()
        monitors.append(themonitor)
    #----------Draw the plot
    thedrawing = onlineMonitor.onlineMonitor_draw()
    thedrawing.setMonitors(monitors)
    curves = [('prePatton15', 0), ('prePatton15', 1), ('prePatton30', 0), ('prePatton30', 1)]
    #thedrawing.draw_paper('online-presn_%s_paper'%method)
    thedrawing.drawEffciency_all('online-presn_eff_%s_%s'%(method, far[0]))
    #thedrawing.drawEffciency('online-presn_eff_%s_%s'%(method, far[0]), curves)
    thedrawing.drawTriggerTime('online-presn_time_%s_%s'%(method, far[0]), curves)
    ##-----------For test-----------
    #for model in ['prePatton30']:
    #    for mo in [1]:
    #        themonitor.readpreSNResultFromTxt(model, mo)
    #        themonitor.timePDF((model, mo))
    ##themonitor.calTime()

    if saveFigs:
        thedrawing.saveFigs()

    plt.show()
    pass

def cmpeffAndTime_presn(model, far, saveFigs=False):
    if model not in ['prePatton15', 'prePatton30']:
        print('Unknow presn model!')
        sys.exit()
    par = {}
    par['SlidingWindow'] = onlineMonitor.par_slidingWindow('presn', far)
    par['TimeInterval'] = onlineMonitor.par_timeInterval('presn', far)
    par['BayesianBlock'] = onlineMonitor.par_bayesianBlock('presn', far)
    monitors = []
    #----------Read the data
    for method in ['SlidingWindow', 'TimeInterval', 'BayesianBlock']:
        themonitor = onlineMonitor.onlineMonitor()
        themonitor.setPar(par[method])
        for mo in [0, 1]:
            themonitor.readpreSNResultFromTxt(model, mo)
        themonitor.calEff()
        themonitor.calTime()
        monitors.append(themonitor)
    #----------Draw the plot
    thedrawing = onlineMonitor.onlineMonitor_draw()
    thedrawing.setMonitors(monitors)
    thedrawing.drawEffciency_cmp('online-presn_eff_cmp_%s'%far, curves=[(model, 0), (model, 1)])
    thedrawing.drawTriggerTime_cmp('online-presn_time_cmp_%s'%far, curves=[(model, 0), (model, 1)])

    if saveFigs:
        thedrawing.saveFigs()

    plt.show()
    pass

if __name__ == '__main__':
    #eff_sn('TimeInterval', ['1permonth'], saveFigs=True)
    effAndTime_presn('TimeInterval', ['1permonth'], saveFigs=True)

    #cmpeff_sn('gar82703', '1peryear', saveFigs=True)
    #cmpeffAndTime_presn('prePatton15', '1peryear', saveFigs=True)
