#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin
#not only for bounce time, but for other checks using promptMOnitor.root

import sys
import os
import promptMonitor
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('HXStyle')

class bounceTime():
    def __init__(self):
        self.par = None
        self.dist = np.arange(10, 500, 20)

        self.bounce_time = {} #(model, mo): [[],[],...,]
        pass

    def setPar(self, thepar):
        if not isinstance(thepar, promptMonitor.par):
            print('Not a legal parameter!')
            sys.exit()
        self.par = thepar
        pass

    def readBounceTime(self, MODEL, MO, saveTXT=False):
        print('Reading the data for %s with MO:%d'%(MODEL, MO))
        topDir = '/junofs/users/huangx/myProject/CCSNMonitor/PromptMonitor/myJob/result'
        import uproot as up
        self.bounce_time[(MODEL, MO)] = []
        for dist in self.dist:
            self.bounce_time[(MODEL, MO)].append([])
            if self.par.method == 'sliding-window':
                indir = topDir + '/sn_%s/%d/%d/%s/sT%d_fT%s_%d'%(MODEL, MO, dist, 'SlidingWindow', self.par.T, self.par.dT, self.par.Nthr)
            elif self.par.method == 'time-interval':
                indir = topDir + '/sn_%s/%d/%d/%s/%d_T%.1f'%(MODEL, MO, dist, 'TimeInterval', self.par.Nthr, self.par.T)
            else:
                print('Do not calculate bounce with method:%s'%self.par.method)
                sys.exit()
            if not saveTXT: #read the data from txt
                infile = indir + '/nevt.txt'
                self.bounce_time[(MODEL, MO)][-1] = np.loadtxt(infile)
            else:
                for ii in range(0, 200):
                    infilename = indir+'/promptTrigger_%d.root'%ii
                    if not os.path.isfile(infilename):
                        print('%s does not exist!'%infilename)
                        continue
                    with up.open(indir+'/promptTrigger_%d.root'%ii) as infile:
                        #trigTree = infile['ttrig']
                        #readin = trigTree.arrays(library='np')
                        #if len(readin['snTriggerTime']) > 1:
                        #    print('Multi triggers found!')
                        #    sys.exit()
                        #elif len(readin['snTriggerTime']) == 0:
                        #    print('Trigger not found!')
                        #    continue
                        #time_trigger = readin['snTriggerTime'][0]
                        evtTree = infile['tevt']
                        readin = evtTree.arrays(library='np')
                        nEvt = len(readin['evtType'])
                        nsum = 0
                        for jj in range(0, nEvt):
                            evttype = readin['evtType'][jj]
                            if evttype != 0: continue
                            nsum += 1
                        self.bounce_time[(MODEL, MO)][-1].append(nsum)
                        #for jj in range(0, nEvt):
                        #    evttype = readin['evtType'][jj]
                        #    if evttype != 0: continue
                        #    evttime = readin['time'][jj]
                        #    if time_trigger-evttime<=self.par.T:
                        #        self.bounce_time[(MODEL, MO)][-1].append(evttime)
                        #        break
            print(self.bounce_time[(MODEL, MO)][-1])
            if saveTXT:
                outfile = indir + '/nevt.txt'
                np.savetxt(outfile, self.bounce_time[(MODEL, MO)][-1])
        pass

    def draw_bouncetime(self):
        fig, ax = plt.subplots()
        model =  'intp3003.data'
        mo = 1
        for ii in [0, 1, 2]:
            data_x = self.bounce_time[(model, mo)][ii]
            ax.hist(data_x, histtype='step', range=[-0.02, 0.08], bins=50, label='Dist:%d'%self.dist[ii])
        ax.set(title='%s:%d'%(model, mo), xlabel='time [s]')
        ax.legend()

        plt.show()
        pass

    def draw_nEvt(self):
        fig, ax = plt.subplots()
        model =  'intp3003.data'
        mo = 0
        for ii in [14, 15, 17, 19]:
            data_x = self.bounce_time[(model, mo)][ii]
            ax.hist(data_x, histtype='step', range=[0, 70], bins=20, label='Dist:%d'%self.dist[ii]) #
        ax.set(title='%s:%d'%(model, mo), xlabel='nEvt')
        ax.legend()

        plt.show()
        pass
    pass

def ana(args, saveFigs=False):
    if args.method not in ['sliding-window', 'time-interval', 'bayesian-block']:
        print('Undefined alert method')
        sys.exit()
    par = None
    if args.method == 'sliding-window':
        par = promptMonitor.par_slidingWindow(args.far)
    elif args.method == 'time-interval':
        par = promptMonitor.par_timeInterval(args.far)
    elif args.method == 'bayesian-block':
        par = promptMonitor.par_bayesianBlock(args.far)
    bounce_time = bounceTime()
    bounce_time.setPar(par)
    bounce_time.readBounceTime(args.model, args.mo, saveTXT=True)
    #bounce_time.draw_nEvt()
    pass

def get_parser():
    import argparse
    parser=argparse.ArgumentParser(description='Calculate the bounce time form prompt monitor')
    parser.add_argument('--method', default='sliding-window', choices=['sliding-window', 'time-interval'], help='The alert method')
    parser.add_argument('--far', default='1permonth', choices=['1peryear', '1permonth'], help='The false alert rate')
    parser.add_argument('--model', default='intp1311.data', choices=['intp1311.data', 'intp3003.data', 'gar81123', 'gar82703'], help='set the log level')
    parser.add_argument('--mo', type=int, default=0, choices=[0,1], help='The mass ordering')

    return parser

if __name__ == '__main__':
    parser=get_parser()
    args=parser.parse_args()

    ana(args, saveFigs=False)
