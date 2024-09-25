#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import promptMonitor
import matplotlib.pyplot as plt

def effAndTime(method, far, saveFigs=False):
    #Draw the alert efficiency and alert time
    if method not in ['sliding-window', 'time-interval', 'bayesian-block']:
        print('Undefined alert method')
        sys.exit()
    monitors = []
    for thisfar in far:
        par = None
        if method == 'sliding-window':
            par = promptMonitor.par_slidingWindow(thisfar)
        elif method == 'time-interval':
            par = promptMonitor.par_timeInterval(thisfar)
        else:
            par = promptMonitor.par_bayesianBlock(thisfar)
        themonitor = promptMonitor.promptMonitor()
        themonitor.setPar(par)
        #----------Read the data
        for model in ['gar81123', 'gar82703', 'intp1311.data', 'intp3003.data']: #
            for mo in [0, 1]:
                themonitor.readPromptResult(model, mo)
        themonitor.calEff()
        themonitor.calTime()
        monitors.append(themonitor)
    #----------Draw the plot
    thedrawing = promptMonitor.promptMonitor_draw()
    thedrawing.setMonitors(monitors)
    #thedrawing.drawEffciency('prompt_eff_%s_%s'%(method, far[0]))
    #thedrawing.drawTriggerTime('prompt_time_%s_%s'%(method, far[0]))
    thedrawing.drawEffciency_all('prompt_eff_%s_%s'%(method, far[0]))
    thedrawing.drawTriggerTime_all('prompt_time_%s_%s'%(method, far[0]))
    #thedrawing.draw_paper('prompt_%s_paper'%method)
    ##-----------For test-----------
    #for model in ['intp3003.data']:
    #    for mo in [0]:
    #        themonitor.readPromptResult(model, mo)
    #        themonitor.timePDF((model, mo))

    if saveFigs:
        thedrawing.saveFigs()

    plt.show()
    pass

def cmpMethod(far, saveFigs=False):
    par = {}
    par['sliding-window'] = promptMonitor.par_slidingWindow(far)
    par['time-interval'] = promptMonitor.par_timeInterval(far)
    par['bayesian-block'] = promptMonitor.par_bayesianBlock(far)
    monitors = []
    #----------Read the data
    for method in ['sliding-window', 'time-interval', 'bayesian-block']:
        themonitor = promptMonitor.promptMonitor()
        themonitor.setPar(par[method])
        for mo in [0, 1]:
            #themonitor.readPromptResult('intp1311.data', mo)
            themonitor.readPromptResult('gar82703', mo)
        themonitor.calEff()
        themonitor.calTime()
        monitors.append(themonitor)
    #----------Draw the plot
    thedrawing = promptMonitor.promptMonitor_draw()
    thedrawing.setMonitors(monitors)
    thedrawing.drawEff_cmp('prompt_eff_cmp_%s'%far)
    thedrawing.drawTime_cmp('prompt_time_cmp_%s'%far)

    if saveFigs:
        thedrawing.saveFigs()

    plt.show()
    pass

if __name__ == '__main__':
    effAndTime('time-interval', ['1peryear'], saveFigs=True)
    #cmpMethod('1peryear', saveFigs=True)
