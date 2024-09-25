#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

from scipy.stats import poisson
from scipy.stats import norm
class calFAR_sliding():
    def __init__(self):
        self.T = 0
        self.dT = 0
        self.r = 0
        self.Nthr = 0
        self.sntype = ''

        self.figs = {} #(fig, ax)

    def setSNType(self, sntype):
        import sys
        self.sntype=sntype
        if sntype=='prompt-sn':
            self.setPar(4, 1e-3, 0.0023, 4)
            pass
        elif sntype=='online-sn':
            self.setPar(10, 1e-1, 148./(24*3600.), 3)
            pass
        elif sntype=='online-presn':
            self.setPar(7*3600, 1*3600, 27.3/(24*3600.), 18)
            pass
        else:
            print('Error: Wrong SN type!')
            sys.exit()

    def setT(self, T):
        self.T = T

    def setdT(self, dT):
        self.dT = dT

    def setBkgRate(self, r):
        self.r = r

    def setThreshold(self, Nthr):
        self.Nthr = Nthr

    def setPar(self, T, dT, r, Nthr):
        self.T = T
        self.dT = dT
        self.r = r
        self.Nthr = Nthr

    def getFAR(self):
        tmpsf=poisson.sf(self.Nthr, self.T*self.r) #Nthr is not included
        #tmpsig=norm.ppf(1-tmpsf)
        tmpsf=(24*3600*30)*tmpsf/self.dT#unit:[month]
        return tmpsf

    def getNthr(self, FAR):
        import numpy as np
        from scipy.stats import poisson
        prob = FAR*self.dT/(30*24*3600.)
        self.Nthr = poisson.isf(prob, self.r*self.T)
        return self.Nthr

    def calFAR(self, nthr):
        far = self.getFAR()
        print('False alert rate for %s with sliding-window method:%.3f per month'%(self.sntype, far))
        return far

    def calNthr(self, FAR):
        nthr = self.getNthr(FAR)
        print('The threshold of sliding-window method for %s:%.1f'%(self.sntype, nthr))
        return nthr

    def drawFAR(self, figName):
        import numpy as np
        import matplotlib.pyplot as plt
        plt.style.use('HXStyle')
        if figName not in self.figs.keys():
            fig, ax = plt.subplots()
            self.figs[figName] = (fig, ax)

        lT = np.arange(1, 7)
        lNthr = np.arange(2, 6)
        self.setdT(1e-3)
        self.setBkgRate(0.0023)
        fig, ax = self.figs[figName]
        for thisT in lT:
            self.setT(thisT)
            lfar = []
            for thisNthr in lNthr:
                self.setThreshold(thisNthr)
                lfar.append(self.getFAR())
            ax.plot(lNthr, lfar, marker='o', label='%.1f s'%thisT)
        ax.hlines(y=[1, 1./12], xmin=2, xmax=5, linestyles='dashed', colors=['gray'])
        ax.set_title(label='$\\rm r_{background}$'+'={:.3f}Hz, dT={}ms'.format(self.r, self.dT*1e3), visible=True)
        ax.set(xlim=[2, 5], ylim=[1e-3, 1e3], yscale='log')
        ax.set_xlabel(xlabel='$\\rm N_{thr}$', x=1, ha='right')
        ax.set_ylabel(ylabel='False alert rate [month]', y=1, ha='right')
        ax.legend(title='T', ncol=2, frameon=True)

class calFAR_bayesian():
    def __init__(self):
        self.ncps = range(1, 12)
        self.nFalseAlert = {} #N_tot:[nfalsealert, ...]
        self.sntype = '' #prompt-sn or online-sn or online-presn
        self.r = 0

        self.figs = {}

    def setSNType(self, sntype):
        import sys
        self.sntype = sntype
        if sntype=='prompt-sn':
            self.r = 196./(24*3600.)
            pass
        elif sntype=='online-sn':
            self.r = 148./(24*3600.)
            pass
        elif sntype=='online-presn':
            self.r = 27.3/(24*3600.)
            pass
        else:
            print('Error: Wrong SN type!')
            sys.exit()

    def getNFalseAlert(self, Nbkg, definition):
        #the background rate in data is 1 Hz
        self.nFalseAlert[Nbkg] = []
        import uproot as up
        print('Reading root files:ncp=', end='')
        for ncp in self.ncps:
            print(ncp, end=', ')
            nfalsealert = 0
            totTrails = 1000
            for fileno in range(0, totTrails):
                infilename = '/junofs/users/huangx/MyProject/Supernova/ccsnMonitor/Analysis/bayesian_block/data/falseAlert/%d/%d/falseAlert_%d.root'%(Nbkg, ncp, fileno)
                with up.open(infilename) as infile:
                    #First, get the time of event for tbeg and tend
                    timetree = infile['time']
                    readin_time = timetree.arrays(library='np')
                    ltime = readin_time['time']
                    ltime.sort()
                    tbeg = ltime[1049] #begin of the Nbkg events
                    tend = ltime[Nbkg+1100-51] #end of the Nbkg events
                    #Then, get the number of false alert in (tbeg, tend)
                    nincrease = 0
                    ndecrease = 0
                    if definition=='increase' or definition=='total':#count the number of increase change point
                        theTree = infile['increase']
                        theReadin= theTree.arrays(library='np')
                        changePoint_t = theReadin['increase_t']
                        firstAlert = theReadin['increase_alertT1']
                        theSize = len(changePoint_t)
                        for ii in range(0, theSize):
                            if self.sntype=='prompt-sn' or self.sntype=='online-sn':
                                if changePoint_t[ii]>tbeg and changePoint_t[ii]<tend and firstAlert[ii]-changePoint_t[ii]<20*self.r:
                                    nincrease+=1
                            elif self.sntype=='online-presn':
                                if changePoint_t[ii]>tbeg and changePoint_t[ii]<tend:
                                    nincrease+=1
                    if definition=='decrease' or definition=='total':#count the number of decrease change point
                        theTree = infile['decrease']
                        theReadin= theTree.arrays(library='np')
                        changePoint_t = theReadin['decrease_t']
                        firstAlert = theReadin['decrease_alertT1']
                        theSize = len(changePoint_t)
                        for ii in range(0, theSize):
                            if self.sntype=='prompt-sn' or self.sntype=='online-sn':
                                if changePoint_t[ii]>tbeg and changePoint_t[ii]<tend and firstAlert[ii]-changePoint_t[ii]<20*self.r:
                                    ndecrease+=1
                            elif self.sntype=='online-presn':
                                if changePoint_t[ii]>tbeg and changePoint_t[ii]<tend:
                                    ndecrease+=1
                    nfalsealert += (nincrease+ndecrease)
            self.nFalseAlert[Nbkg].append(nfalsealert/float(totTrails))
        print()

    def saveNFalseAlert(self):
        import numpy as np
        outfilename = '/junofs/users/huangx/myProject/CCSNMonitor/Analysis/myJob/nfalsealert_%s.npy'%self.sntype
        np.save(outfilename, self.nFalseAlert)

    def readNFalseAlert(self):
        import numpy as np
        infilename = '/junofs/users/huangx/myProject/CCSNMonitor/Analysis/myJob/nfalsealert_%s.npy'%self.sntype
        self.nFalseAlert = np.load(infilename, allow_pickle=True).item()

    def drawFAR(self):
        import matplotlib.pyplot as plt
        plt.style.use('HXStyle')
        fig, ax = plt.subplots()
        self.figs['false alert rate'] = (fig, ax)
        for nbkg in [3000, 5000]:
            ax.plot(self.ncps, self.nFalseAlert[nbkg], label='N=%d'%nbkg, linestyle='dashed')
        ax.legend()
        ax.set(title='Number of false alerts', xlabel='ncp_prior', ylabel='$N_{blocks}$', yscale='log')

    def calFAR(self, NCP, rbkg=None):
        if rbkg==None:
            rbkg = self.r
        import numpy as np
        #unit of false alert is /month
        if 5000 not in self.nFalseAlert.keys():
            self.getNFalseAlert(5000, 'increase')
        data_ncp = self.ncps
        data_far = (30*24*3600)*rbkg*np.array(self.nFalseAlert[5000])/5000.
        from scipy import interpolate
        intpfunc = interpolate.interp1d(data_ncp, data_far)
        thisfar = intpfunc(NCP)
        print('The false alert rate corresponding to ncp_prior:%.2f is %.2f/month'%(NCP, thisfar))
        return thisfar

    def calNCP(self, FAR, methodOpt='fit', rbkg=None):
        if rbkg==None:
            rbkg = self.r
        import numpy as np
        #unit of false alert is /month
        if 5000 not in self.nFalseAlert.keys():
            self.getNFalseAlert(5000, 'increase')
        data_ncp = self.ncps
        data_far = (30*24*3600)*rbkg*np.array(self.nFalseAlert[5000])/5000.
        if methodOpt == 'interp':
            #---------------for linear interpolate-------------
            from scipy import interpolate
            intpfunc = interpolate.interp1d(data_far, data_ncp)
            thisncp = intpfunc(FAR)
        elif methodOpt == 'fit':
            #---------------for linear fit-------------
            k0=-1.
            k1=3.
            def fitfunc(x, p0, p1):
                y=p0*x+p1
                return y
            from scipy.optimize import curve_fit
            popt, pcov=curve_fit(fitfunc, np.log10(data_far[-6:]), data_ncp[-6:], p0=[k0, k1], absolute_sigma=True)#, sigma=1./np.sqrt(y)
            thisncp = popt[0]*np.log10(FAR)+popt[1]
        print('The ncp_prior corresponding to false alert rate:%.2f/month is %.2f'%(FAR, thisncp))
        return thisncp

if __name__ == '__main__':
    sntype = 'online-presn'
    #For the sliding-window method
    calfar = calFAR_sliding()
    calfar.setSNType(sntype)
    nthr = calfar.calNthr(1/12.)
    far = calfar.calFAR(nthr)

    #For the bayesian-block method
    calfar = calFAR_bayesian()
    calfar.setSNType(sntype)
    calfar.readNFalseAlert()
    ncp = calfar.calNCP(far, methodOpt='fit') #false alert rate to be the same as sliding-window method
    #far = calfar.calFAR(ncp)
