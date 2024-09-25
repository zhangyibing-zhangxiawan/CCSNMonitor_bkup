#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import sys
import numpy as np
import math
import matplotlib.pyplot as plt
plt.style.use('HXStyle')

class cmpSK():
    def __init__(self):
        self.sntype = 'sn' #'sn' or 'pre-sn'
        self.curve_juno = {} # key: [[dist], [eff]]
        self.curve_juno_skbkg = {} # key: [[dist], [eff]]
        self.curve_sk = {}
        self.key_juno = {
                'Nakazato13_IO':('intp1311.data', 0), 'Nakazato13_NO':('intp1311.data', 1),
                'Patton15_IO':('prePatton15', 0), 'Patton15_NO':('prePatton15', 1)
                }
        self.tagEff = [1]
        self.key_sk = {
                'Nakazato13_IO':'Nakazato_13M_IO', 'Nakazato13_NO':'Nakazato_13M_NO',
                'Patton15_IO':'Patton_15M_IO_up', 'Patton15_NO':'Patton_15M_NO_up'
                }

        #Options for drawing
        self.figs = {} #figName: (fig, ax)
        self.label_mo = {0:'IO', 1:'NO'}
        self.label_model = {'Nakazato13':'Nakazato, $\\rm13M_{\odot}$', 'Nakazato30':'Nakazato, $\\rm30M_{\odot}$'}
        pass

    def setSNType(self, thetype):
        if thetype not in ['sn', 'presn']:
            print('ERROR: Unknow SN type!')
            sys.exit()
        self.sntype = thetype

    #Fit functions are for getting the curve for JUNO
    def fitfunc1(self, x, A, nthr):
        from scipy.stats import poisson
        mu=A/(x**2)
        prob=poisson.sf(nthr, mu)
        return prob

    def fitfunc2(self, x, A, alpha, nthr, p2):
        from scipy.stats import poisson
        mu=A/(x**2)+alpha
        prob1=poisson.sf(nthr, mu)
        prob=prob1+(1-prob1)*p2
        return prob

    def readJUNO(self, key):
        if self.sntype == 'sn': #use fitfunc1
            dist = np.linspace(10, 500, 200)
            #fitpar = {('intp1311.data', 0):3, ('intp1311.data', 1):3, ('intp3003.data', 0):3, ('intp3003.data', 1):3}
            #A = {('intp1311.data', 0): 226320.1, ('intp1311.data', 1):180421.5, ('intp3003.data', 0):100000, ('intp3003.data', 1):100000}
            fitpar = {('intp1311.data', 0):5, ('intp1311.data', 1):6, ('intp3003.data', 0):5, ('intp3003.data', 1):5}
            A = {('intp1311.data', 0):236758.4, ('intp1311.data', 1):232449.6, ('intp3003.data', 0):100000, ('intp3003.data', 1):100000}
            fitfunc = lambda x : self.fitfunc1(x, A[key], fitpar[key])
            for tageff in self.tagEff:
                eff = fitfunc(1./math.sqrt(tageff)*dist)
                self.curve_juno[(key, tageff)] = [dist, eff]
            #--------------------------------------------
            dist = np.linspace(10, 200, 200)
            #fitpar = {('intp1311.data', 0):25, ('intp1311.data', 1):25, ('intp3003.data', 0):25, ('intp3003.data', 1):25}
            #A = {('intp1311.data', 0): 255146.8, ('intp1311.data', 1):197512.1, ('intp3003.data', 0):100000, ('intp3003.data', 1):100000}
            fitpar = {('intp1311.data', 0):25, ('intp1311.data', 1):25, ('intp3003.data', 0):25, ('intp3003.data', 1):25}
            A = {('intp1311.data', 0): 255146.8, ('intp1311.data', 1):197512.1, ('intp3003.data', 0):100000, ('intp3003.data', 1):100000}
            fitfunc = lambda x : self.fitfunc1(x, A[key], fitpar[key])
            for tageff in self.tagEff:
                eff = fitfunc(1./math.sqrt(tageff)*dist)
                self.curve_juno_skbkg[(key, tageff)] = [dist, eff]
        elif self.sntype == 'presn': #use fitfunc2
            dist = np.linspace(0.1, 2.0, 200)
            fitpar = {('prePatton15', 0):(16, 0.0027), ('prePatton15', 1):(17, 0.0027), ('prePatton30', 0):(17, 0.0027), ('prePatton30', 1):(17, 0.0027)} #fit par for 1peryear
            A = {('prePatton15', 0):3.216418, ('prePatton15', 1):13.169087, ('prePatton30', 0):8.738525, ('prePatton30', 1):27.408676} #fit par for 1peryear
            alpha = {('prePatton15', 0):6.34, ('prePatton15', 1):6.34, ('prePatton30', 0):6.34, ('prePatton30', 1):6.34} #fit par for 1peryear
            fitfunc = lambda x : self.fitfunc2(x, A[key], alpha[key], fitpar[key][0], fitpar[key][1])
            eff = fitfunc(dist)
            self.curve_juno[key] = [dist, eff]

    def readSK(self, key):
        sktop = '/junofs/users/huangx/myProject/CCSNMonitor/OnlineMonitor/OnlineMonitor/share/Ana/SK'
        infileName = sktop + '/%s.csv'%key
        thecurve = np.loadtxt(infileName, delimiter=', ')
        self.curve_sk[key] = [thecurve[:, 0], thecurve[:, 1]]

    def compare(self):
        if self.sntype == 'sn':
            self.cmpSN()
        elif self.sntype == 'presn':
            self.cmpPreSN()
        else:
            print('ERROR: Unknow sn type')
            sys.exit()
        pass

    def cmpSN(self):
        figName = 'cmpSK_sn'
        if figName in self.figs.keys():
            fig, ax = self.figs[figName]
        else:
            fig, ax = plt.subplots()
            self.figs[figName] = (fig, ax)

        LINESTYLE = ['dashed', 'solid']
        COLORS=[]
        for color in plt.rcParams['axes.prop_cycle']:
            COLORS.append(color['color'])
        COLORS = ['#1f77b4', '#d62728', '#ff7f0e']

        for model in ['Nakazato13']:
            for mo in [0, 1]:
                key_sk = self.key_sk['%s_%s'%(model, self.label_mo[mo])]
                self.readSK(key_sk)
                ax.plot(self.curve_sk[key_sk][0], self.curve_sk[key_sk][1], linestyle=LINESTYLE[mo], color=COLORS[0], lw=5, label='SK, $\\rm FAR\ 2\\times 10^{-6}/year$, %s'%self.label_mo[mo])
        colorforeff = [1, 6, 9]
        neff = -1
        for tageff in self.tagEff:
            neff += 1
            for model in ['Nakazato13']:
                for mo in [0, 1]:
                    key_juno = self.key_juno['%s_%s'%(model, self.label_mo[mo])]
                    self.readJUNO(key_juno)
                    key = (key_juno, tageff)
                    ax.plot(self.curve_juno[key][0], self.curve_juno[key][1], linestyle=LINESTYLE[mo], color=COLORS[1], lw=5, label='JUNO, $\\rm FAR\ 2\\times 10^{-6}/year$, %s'%self.label_mo[mo]) #'%d'%int(tageff*100)+'%'+ colorforeff[neff]
        neff = -1
        for tageff in self.tagEff:
            neff += 1
            for model in ['Nakazato13']:
                for mo in [0, 1]:
                    key_juno = self.key_juno['%s_%s'%(model, self.label_mo[mo])]
                    self.readJUNO(key_juno)
                    key = (key_juno, tageff)
                    ax.plot(self.curve_juno_skbkg[key][0], self.curve_juno_skbkg[key][1], linestyle=LINESTYLE[mo], color=COLORS[2], lw=5, label='JUNO, with SK parameter, %s'%self.label_mo[mo]) #'%d'%int(tageff*100)+'%'+colorforeff[neff] with increased bkg
        ax.set(xlim=[0, 550], ylim=[0, 1.05], title='SN neutrino with Nakazato, $\\rm13M_{\odot}$ model')
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert effciency', y=1, ha='right')
        ax.legend(ncol=1, loc='upper right', fontsize=20) #, bbox_to_anchor=(0.5, 1.07))
        pass

    def cmpPreSN(self):
        figName = 'cmpSK_presn'
        if figName in self.figs.keys():
            fig, ax = self.figs[figName]
        else:
            fig, ax = plt.subplots()
            self.figs[figName] = (fig, ax)

        LINESTYLE = ['dashed', 'solid']
        COLORS=[]
        for color in plt.rcParams['axes.prop_cycle']:
            COLORS.append(color['color'])
        COLORS = ['#1f77b4', '#d62728', '#ff7f0e']

        for mo in [0, 1]:
            for model in ['Patton15']:
                key_sk = self.key_sk['%s_%s'%(model, self.label_mo[mo])]
                self.readSK(key_sk)
                ax.plot(self.curve_sk[key_sk][0], self.curve_sk[key_sk][1], linestyle=LINESTYLE[mo], color=COLORS[0], lw=5, label='SK-Gd, %s'%self.label_mo[mo])
                key_juno = self.key_juno['%s_%s'%(model, self.label_mo[mo])]
                self.readJUNO(key_juno)
                ax.plot(self.curve_juno[key_juno][0], self.curve_juno[key_juno][1], linestyle=LINESTYLE[mo], color=COLORS[1], lw=5, label='JUNO, %s'%self.label_mo[mo])
        ax.text(1.1, 0.8, '$\\rm \\bf{preSN\ neutrino}$\nPatton, $\\rm15M_{\odot}$ model\nFAR<1/year', size=30)
        ax.set(ylim=[0, 1.05])
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert effciency', y=1, ha='right')
        ax.legend(ncol=2, loc='center', bbox_to_anchor=(0.5, 1.07))
        pass

    def saveFigs(self):
        for thisfigName, thisfig in self.figs.items():
            thisfig[0].savefig('/junofs/users/huangx/myProject/CCSNMonitor/figures2/'+thisfigName+'.eps')
            thisfig[0].savefig('/junofs/users/huangx/myProject/CCSNMonitor/figures2/'+thisfigName+'.svg')

if __name__ == '__main__':
    thecmp = cmpSK()
    thecmp.setSNType('sn')
    thecmp.compare()
    thecmp.saveFigs()

    plt.show()
