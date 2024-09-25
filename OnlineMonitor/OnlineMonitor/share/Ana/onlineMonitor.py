#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import sys
import os
import numpy as np

class par():
    def __init__(self, sntype, method, far):
        self.dist = {}
        self.toybkg = False
        self._setSnType(sntype)
        self._setMethod(method)
        self._setFAR(far)
        pass

    def _setSnType(self, sntype):
        if sntype == 'sn':
            self.dist[('intp1311.data', 0)] = np.arange(10, 600, 20)
            self.dist[('intp1311.data', 1)] = np.arange(10, 600, 20)
            self.dist[('intp3003.data', 0)] = np.arange(10, 600, 20)
            self.dist[('intp3003.data', 1)] = np.arange(10, 600, 20)
            self.dist[('gar81123', 0)] = np.arange(10, 600, 20)
            self.dist[('gar81123', 1)] = np.arange(10, 600, 20)
            self.dist[('gar82703', 0)] = np.arange(10, 600, 20)
            self.dist[('gar82703', 1)] = np.arange(10, 600, 20)
            self.toybkg = False
            pass
        elif sntype == 'presn':
            self.dist[('prePatton15', 0)] = np.arange(0.1, 1.55, 0.1)
            self.dist[('prePatton15', 1)] = np.arange(0.1, 1.55, 0.1)
            self.dist[('prePatton30', 0)] = np.arange(0.1, 1.55, 0.1)
            self.dist[('prePatton30', 1)] = np.arange(0.1, 2.05, 0.1)
            #self.dist[('prePatton15', 0)] = [0.15]
            #self.dist[('prePatton15', 1)] = [0.15]
            #self.dist[('prePatton30', 0)] = [0.25]
            #self.dist[('prePatton30', 1)] = [0.25]
            self.toybkg = True
            pass
        else:
            print('Unknow sntype!')
            sys.exit()
        self.sntype = sntype
        pass

    def _setMethod(self, method):
        themethods = ['SlidingWindow', 'TimeInterval', 'BayesianBlock']
        themethod_names = {'SlidingWindow':'Sliding window', 'TimeInterval':'Sliding event', 'BayesianBlock':'Bayesian blocks'}
        if method not in themethods:
            print('Unknow alert method!')
            sys.exit()
        self.method = method
        self.method_name = themethod_names[method]
        if method == 'BayesianBlock':
            self.toybkg = True
        pass

    def _setFAR(self, far):
        thefars = ['1permonth', '1peryear', 'cmpSK']
        thefar_names = {'1permonth':'1/month', '1peryear':'1/year', 'cmpSK':'SK_FAR'}
        if far not in thefars:
            print('Unknow false alert rate!')
            sys.exit()
        self.far = far
        self.far_name = thefar_names[far]
        pass
    pass

class par_slidingWindow(par):
    def __init__(self, sntype, far):
        super().__init__(sntype, 'SlidingWindow', far)
        if self.sntype == 'sn':
            self.T = 10
            self.dT = '1e-1'
            self.Nthr = 0
            if self.far == '1permonth':
                self.Nthr = 2
            elif self.far == '1peryear':
                self.Nthr = 3
            elif self.far == 'cmpSK':
                self.T = 20
                self.Nthr = 25
        elif self.sntype == 'presn':
            self.T = 7*3600
            self.dT = 1*3600
            self.Nthr = 0
            if self.far == '1permonth':
                self.Nthr = 14
            elif self.far == '1peryear':
                self.Nthr = 17
        pass
    pass

class par_timeInterval(par):
    def __init__(self, sntype, far):
        super().__init__(sntype, 'TimeInterval', far)
        if self.sntype == 'sn':
            self.Nthr = 2
            self.T = 0
            if self.far == '1permonth':
                self.T = 15.8
            elif self.far == '1peryear':
                self.T = 4.5
            elif self.far == 'cmpSK':
                self.Nthr = 5
                self.T = 15.2
        elif self.sntype == 'presn':
            self.Nthr = 17
            self.T = 0
            if self.far == '1permonth':
                self.T = 9.5*3600
            elif self.far == '1peryear':
                self.T = 7.3*3600
        pass
    pass

class par_bayesianBlock(par):
    def __init__(self, sntype, far):
        super().__init__(sntype, 'BayesianBlock', far)
        self.ncp_prior = 0
        if self.sntype == 'sn':
            if self.far == '1permonth':
                self.ncp_prior = 8.5
            elif self.far == '1peryear':
                self.ncp_prior = 11.2
        elif self.sntype == 'presn':
            if self.far == '1permonth':
                self.ncp_prior = 7.4
            elif self.far == '1peryear':
                self.ncp_prior = 10.1
        pass
    pass

class onlineMonitor():
    def __init__(self):
        self.par = None

        #the original data
        #self.alertTime = {} #(model, mo):[[], [], ..]
        self.alertTime = {} #(model, mo):{'dist':[[], .., []], ...}

        #Alert efficiency and alert time
        self.eff = {} #(model, mo):[]
        self.eff_err = {} #(model, mo):[]
        self.time = {} #(model, mo):[]
        self.time_err = {} #(model, mo):[]

    def getDist(self, key):
        return self.par.dist[key]

    def getEff(self, key):
        return self.eff[key], self.eff_err[key]

    def getTime(self, key):
        return self.time[key], self.time_err[key]

    def getMethod(self):
        return self.par.method

    def setPar(self, thepar):
        if not isinstance(thepar, par):
            print('Not a legal parameter!')
            sys.exit()
        self.par = thepar
        pass

    def readSNResult(self, MODEL, MO):
        import uproot as up
        topDir = '/junofs/users/huangx/myProject/CCSNMonitor/OnlineMonitor/OnlineMonitor/myJob/result_%s_36GW'%self.method
        #topDir = '/junofs/users/huangx/myProject/CCSNMonitor/OnlineMonitor/OnlineMonitor/myJob/result_%s'%self.method
        self.alertTime[(MODEL, MO)] = {}
        print('Reading data of distance:', end=' ')
        for dist in self.dist[(MODEL, MO)]:
            self.alertTime[(MODEL, MO)][dist] = []
            print('%.1fkpc'%dist, end=', ')
            indir = topDir + '/sn_%s/%d/%d/%s'%(MODEL, MO, dist, self.method)
            if self.method=='SlidingWindow':
                indir += '/sT%d_fT%s_%d'%(self.T, self.dT, self.Nthr[self.far])
            elif self.method=='BayesianBlock':
                indir += '/ncp%.1f'%self.ncp_prior[self.far]
            else:
                print('Error: Unknow method')
                sys.exit()
            indir += '/toybkg%d'%self.toybkg
            for ith in range(0, 200):
                infilename = indir+'/user_sn_%d.root'%ith
                if not os.path.isfile(infilename):
                    print('Warning: File does not exist: (%.1fkpc, %dth)'%(dist, ith))
                    continue
                with up.open(infilename) as infile:
                    alertTree = infile['alert_sn']
                    readin = alertTree.arrays(library='np')
                    if len(readin['alertStatus'])>2:
                        print('Error: Unknow behavior for the %dth trail'%ith)
                        sys.exit()
                    if len(readin['alertStatus'])>0:
                        tmptime = readin['alertTime'][0]
                        self.alertTime[(MODEL, MO)][dist].append([tmptime])
                    else:
                        self.alertTime[(MODEL, MO)][dist].append([])

    def readSNResultFromTxt(self, MODEL, MO):
        import uproot as up
        topdir = '/junofs/users/huangx/myProject/CCSNMonitor/OnlineMonitor/OnlineMonitor/myJob'
        self.alertTime[(MODEL, MO)] = {}
        print('Reading data of distance:', end=' ')
        for dist in self.par.dist[(MODEL, MO)]:
            indir = topdir + '/result/sn_%s/%d/%d/%s'%(MODEL, MO, dist, self.par.method)
            self.alertTime[(MODEL, MO)][dist] = []
            print('%dkpc'%dist, end=', ', flush=True)
            if self.par.method == 'SlidingWindow':
                indir += '/sT%d_fT%s_%d'%(self.par.T, self.par.dT, self.par.Nthr)
            elif self.par.method == 'TimeInterval':
                indir += '/%d_T%.1f'%(self.par.Nthr, self.par.T)
            elif self.par.method == 'BayesianBlock':
                indir += '/ncp%.1f'%self.par.ncp_prior
            indir += '/toybkg%d'%self.par.toybkg

            infilename = indir + '/times.txt'
            if not os.path.isfile(infilename):
                print('Warning: File does not exist: %s'%infilename)
                continue
            with open(infilename, 'rb') as infile:
                for oneline in infile.readlines():
                    onelinestr = oneline.strip()
                    timelist = onelinestr.split()
                    timelist = [float(x) for x in timelist]
                    self.alertTime[(MODEL, MO)][dist].append(timelist)
        print()
        pass

    def readpreSNResult(self, MODEL, MO):
        import uproot as up
        topDir = '/junofs/users/huangx/myProject/CCSNMonitor/OnlineMonitor/OnlineMonitor/myJob/result_%s'%self.method
        self.alertTime[(MODEL, MO)] = {}
        print('Reading data of distance:', end=' ')
        for dist in self.dist[(MODEL, MO)]:
            self.alertTime[(MODEL, MO)][dist] = []
            print('%.1fkpc'%dist, end=', ', flush=True)
            indir = topDir + '/presn_%s/%d/%.1f/%s'%(MODEL, MO, dist, self.method)
            if self.method=='SlidingWindow':
                indir += '/sT%d_fT%s_%d'%(self.T, self.dT, self.Nthr[self.far])
            elif self.method=='BayesianBlock':
                indir += '/ncp%.1f'%self.ncp_prior[self.far]
            else:
                print('Error: Unknow method')
                sys.exit()
            indir += '/toybkg%d'%self.toybkg
            for ith in range(0, 200):
                infilename = indir+'/%dth/user_presn.root'%ith
                if not os.path.isfile(infilename):
                    print('Warning: File does not exist: (%.1fkpc, %dth)'%(dist, ith))
                    continue
                with up.open(infilename) as infile:
                    alertTree = infile['alert_presn']
                    readin = alertTree.arrays(library='np')
                    totalert = len(readin['alertStatus'])
                    if totalert>100:
                        print('Error: Unknow behavior for the %dth trail'%ith)
                        sys.exit()
                    time_ith = [] #len==100
                    for jth in range(0, totalert):
                        if readin['alertStatus'][jth]==1:
                            time_ith.append(readin['alertTime'][jth])
                        else:
                            print('Error: Unknow alert status for the %dth trail'%ith)
                            sys.exit()
                    self.alertTime[(MODEL, MO)][dist].append(time_ith)
        print()

    def readpreSNResultFromTxt(self, MODEL, MO):
        import uproot as up
        topDir = '/junofs/users/huangx/myProject/CCSNMonitor/OnlineMonitor/OnlineMonitor/myJob/result' #_%s_36GW%self.method #_36GW
        self.alertTime[(MODEL, MO)] = {}
        print('Reading data of distance:', end=' ')
        for dist in self.par.dist[(MODEL, MO)]:
            self.alertTime[(MODEL, MO)][dist] = []
            print('%.1fkpc'%dist, end=', ', flush=True)
            #indir = topDir + '/presn_%s/%d/%.1f/%s'%(MODEL, MO, dist, self.par.method)
            indir = topDir + '/presn_%s/%d/%.1f/%s'%(MODEL, MO, dist, self.par.method)
            if self.par.method=='SlidingWindow':
                indir += '/sT%d_fT%s_%d'%(self.par.T, self.par.dT, self.par.Nthr)
            elif self.par.method=='TimeInterval':
                indir += '/%d_T%d'%(self.par.Nthr, self.par.T)
            elif self.par.method=='BayesianBlock':
                indir += '/ncp%.1f'%self.par.ncp_prior
            else:
                print('Error: Unknow method')
                sys.exit()
            indir += '/toybkg%d'%self.par.toybkg

            infilename = indir + '/times.txt'
            if not os.path.isfile(infilename):
                print('Warning: File does not exist: %s'%infilename)
                continue
            with open(infilename, 'rb') as infile:
                for oneline in infile.readlines():
                    onelinestr = oneline.strip()
                    timelist = onelinestr.split()
                    timelist = [float(x) for x in timelist]
                    self.alertTime[(MODEL, MO)][dist].append(timelist)
        print()

    def calEff(self, totN=100):
        import math
        #keys = sorted(self.alertTime.keys())
        keys = self.alertTime.keys()
        for key in keys:
            value = self.alertTime[key]
            self.eff[key] = []
            self.eff_err[key] = []
            for dist, times in value.items():
                eff = []
                for time_ith in times:
                    pith = len(time_ith)/float(totN)
                    eff.append(pith)
                #thiseff = np.mean(eff)
                thiseff = sum(eff)/200.
                thiserr = math.sqrt(thiseff*(1-thiseff)/float(len(eff)))
                if thiserr == 0:
                    thiserr = 1./200.
                self.eff[key].append(thiseff)
                self.eff_err[key].append(thiserr)
        #print(self.eff)
        #print(self.eff_err)

    def _get_fit_par(self):
        fitpar = {}
        if self.par.sntype == 'sn':
            nthr = 2
            if self.par.far=='1peryear' and self.par.method=='SlidingWindow': nthr = 3
            elif self.par.far=='cmpSK' and self.par.method=='SlidingWindow': nthr = 25
            elif self.par.far=='cmpSK' and self.par.method=='TimeInterval': nthr = 6
            for key in [('gar81123', 0), ('gar81123', 1), ('gar82703', 0), ('gar82703', 1), ('intp1311.data', 0), ('intp1311.data', 1), ('intp3003.data', 0), ('intp3003.data', 1)]:
                fitpar[key] = nthr
            if self.par.far=='1peryear' and self.par.method=='BayesianBlock': fitpar[('gar82703', 0)] = 3
        elif self.par.sntype == 'presn':
            if self.par.far == '1permonth':
                if self.par.method == 'TimeInterval':
                    fitpar[('prePatton15', 0)] = (16, 8.35, 0.0328)
                    fitpar[('prePatton15', 1)] = (17, 8.35, 0.0328)
                    fitpar[('prePatton30', 0)] = (17, 8.35, 0.0328)
                    fitpar[('prePatton30', 1)] = (17, 8.35, 0.0328)
                if self.par.method == 'SlidingWindow':
                    fitpar[('prePatton15', 0)] = (14, 6.13, 0.0312)
                    fitpar[('prePatton15', 1)] = (14, 6.13, 0.0312)
                    fitpar[('prePatton30', 0)] = (14, 6.13, 0.0312)
                    fitpar[('prePatton30', 1)] = (14, 6.13, 0.0312)
                if self.par.method == 'BayesianBlock':
                    fitpar[('prePatton15', 0)] = (14, 6.13, 0.0312)
                    fitpar[('prePatton15', 1)] = (14, 6.13, 0.0312)
                    fitpar[('prePatton30', 0)] = (13, 6.13, 0.0312)
                    fitpar[('prePatton30', 1)] = (13, 6.13, 0.0312)
            elif self.par.far == '1peryear':
                if self.par.method == 'TimeInterval':
                    fitpar[('prePatton15', 0)] = (16, 6.34, 0.0027)
                    fitpar[('prePatton15', 1)] = (17, 6.34, 0.0027)
                    fitpar[('prePatton30', 0)] = (17, 6.34, 0.0027)
                    fitpar[('prePatton30', 1)] = (17, 6.34, 0.0027)
                if self.par.method == 'SlidingWindow':
                    fitpar[('prePatton15', 0)] = (17, 6.13, 0.0020)
                    fitpar[('prePatton15', 1)] = (17, 6.13, 0.0020)
                    fitpar[('prePatton30', 0)] = (17, 6.13, 0.0020)
                    fitpar[('prePatton30', 1)] = (17, 6.13, 0.0020)
                if self.par.method == 'BayesianBlock':
                    fitpar[('prePatton15', 0)] = (17, 6.13, 0.0027)
                    fitpar[('prePatton15', 1)] = (17, 6.13, 0.0027)
                    fitpar[('prePatton30', 0)] = (16, 6.13, 0.0027)
                    fitpar[('prePatton30', 1)] = (15, 6.13, 0.0027)
        return fitpar

    def fit_eff(self, key):
        # = Fit the efficiency curve =
        print('Fitting the efficiency curve: (%s, %d)...'%(key[0],key[1]))
        fitpar = self._get_fit_par()
        if self.par.sntype == 'sn':
            def fitfunc(x, A):
                nthr = fitpar[key]
                from scipy.stats import poisson
                mu=A/(x**2)
                prob=poisson.sf(nthr, mu)
                return prob
            vp0 = 1000
        elif self.par.sntype == 'presn':
            def fitfunc(x, A):
                alpha = fitpar[key][1]
                nthr = fitpar[key][0]
                p2 = fitpar[key][2]
                from scipy.stats import poisson
                mu=A/(x**2)+alpha
                prob1=poisson.sf(nthr, mu)
                prob=prob1+(1-prob1)*p2
                return prob
            vp0 = 1
        else:
            print("Error: Wrong sntype!")
            sys.exit()
        from scipy.optimize import curve_fit
        popt, pcov = curve_fit(fitfunc, self.getDist(key), self.eff[key], sigma=self.eff_err[key], p0=(vp0), absolute_sigma=True) #2e5
        rfunc = lambda x : fitfunc(x, popt[0])
        print('Best fit value:%.1f'%popt[0], end='')
        r=np.array(self.eff[key])-rfunc(self.getDist(key))
        chi_square=np.sum((r/np.array(self.eff_err[key]))**2)
        print('    chi square:%.2f'%chi_square)

        # = Calculate the alert distance =
        if True:
            def calDist(thefunc):
                from scipy.optimize import root_scalar
                f =lambda x : thefunc(x) - 0.5
                sol = root_scalar(f, bracket=[0.1, 500], method='brentq')
                return sol.root
            solroot = calDist(rfunc)
            from scipy.stats import norm
            k0 = popt[0]
            kerr = np.sqrt(pcov[0][0])
            tmpdist = []
            for ith in range(0, 1000):
                tmpk = norm.rvs(loc=k0, scale=kerr)
                thisfunc = lambda x : fitfunc(x, tmpk)
                tmpdist.append(calDist(thisfunc))
            solroot_err = np.sqrt(np.var(tmpdist))
            print('Alert efficiency reach 50%% at %.3f+-%.3fkpc'%(solroot, solroot_err))
        return rfunc

    def calTime(self):
        #keys = sorted(self.alertTime.keys())
        keys = self.alertTime.keys()
        for key in keys:
            value = self.alertTime[key]
            self.time[key] = []
            self.time_err[key] = []
            for dist, times in value.items():
                #print('Distance:%.1f'%dist)
                thetime = []
                for time_ith in times:
                    thetime.extend(time_ith)
                thetime = np.array(thetime)
                thetime.sort()
                orderStatistics = 0
                if len(thetime)==0:
                    print('Warn: the length of times is 0')
                    continue
                p_cl = 0.68
                N = len(thetime)
                orderStatistics = thetime[int(N*p_cl)]
                def func_pdf(x):
                    cont, edges = np.histogram(thetime, bins=100, density=True)
                    bincenter = (edges[:-1]+edges[1:])/2.
                    #Find the index of bin at which x is located
                    if x<bincenter[0]: x = bincenter[0]
                    if x>bincenter[-1]: x = bincenter[-1]
                    idx = 0
                    while idx<len(bincenter):
                        if x<bincenter[idx]: break
                        idx += 1
                    idx -= 1
                    if idx+1<len(bincenter):
                        center_beg = bincenter[idx]
                        center_end = bincenter[idx+1]
                        rval = cont[idx] + (x-center_beg)*(cont[idx+1]-cont[idx])/(center_end-center_beg)
                    elif idx+1 == len(bincenter):
                        rval = cont[-1]
                    else:
                        print('Warning')
                        sys.exit()
                    return rval
                if len(thetime)<50*100:
                    orderStatistics_err = 0
                else:
                    thepdf = func_pdf(orderStatistics)
                    orderStatistics_err = np.sqrt(100*p_cl*(1-p_cl)/(thepdf*thepdf)/N)
                self.time[key].append(orderStatistics)
                self.time_err[key].append(orderStatistics_err)
            #print('Time for %s with MO%d:'%(key[0], key[1]))
            #print(np.array(self.time[key])/3600.)
            #print(np.array(self.time_err[key])/3600.)

    def fit_time(self, key):
        pass

    #---------------------For test---------------------
    def timePDF(self, curve):
        import matplotlib.pyplot as plt
        plt.style.use('HXStyle')

        value = self.alertTime[curve]
        ith = 0
        for dist, times in value.items():
            thetime = []
            for time_ith in times:
                #avetime = np.mean(time_ith)
                #thetime.append(avetime)
                thetime.extend(time_ith)
                break
            fig, ax = plt.subplots()
            ax.set(title='dist=%.1fkpc'%dist)
            ax.hist(thetime, weights=len(thetime)*[1./100.], bins=100, histtype='step') #, range=[-1.5e5, 0]
            #ax.hist(times[0], bins=20, histtype='step') #, range=[-1.5e5, 0]
            #ax.hist(times[20], bins=20, histtype='step') #, range=[-1.5e5, 0]
            #ax.hist(times[70], bins=20, histtype='step') #, range=[-1.5e5, 0]
            ith += 1
            if ith>7: break
            #break
        plt.show()
        pass
    pass

import matplotlib.pyplot as plt
plt.style.use('HXStyle')

class onlineMonitor_draw():
    def __init__(self):
        self.monitors = []
        self.monitor = None

        #fit options
        self.fitopt = 1 #1:fitfunc1 2:fitfunc2
        self.fitpar = {}

        self.figs = {} #figName: (fig, ax)

        #drawing settings
        COLORS=[]
        for color in plt.rcParams['axes.prop_cycle']:
            COLORS.append(color['color'])
        COLORS = ['#1f77b4', '#d62728', '#ff7f0e', '#9467bd']
        self.COLOR_model = {'intp1311.data':COLORS[0], 'intp3003.data':COLORS[1],
                'gar81123':COLORS[2], 'gar82703':COLORS[3],
                'prePatton15':COLORS[0], 'prePatton30':COLORS[1]}
        self.COLOR_mo = {0:COLORS[0], 1:COLORS[1]}
        self.COLOR_method = [COLORS[0], COLORS[1], COLORS[2]]
        self.MARKER_model = {'intp1311.data':'.', 'intp3003.data':'*',
                'gar81123':'.', 'gar82703':'*',
                'prePatton15':'.', 'prePatton30':'*'}
        self.LINESTYLE_model = {'intp1311.data':'dashed', 'intp3003.data':'solid',
                'gar81123':'dashed', 'gar82703':'solid',
                'prePatton15':'dashed', 'prePatton30':'solid'}
        self.LINESTYLE_mo = {0:'dashed', 1:'solid'}
        self.LABEL_model = {'gar82703':'Garching', 'gar81123':'Garching', 'intp1311.data':'Nakazato', 'intp3003.data':'Nakazato', 'prePatton15':'Patton', 'prePatton30':'Patton'}
        self.LABEL_mass = {'gar82703':'$\\rm27M_{\odot}$', 'gar81123':'$\\rm11M_{\odot}$', 'intp1311.data':'$\\rm13M_{\odot}$', 'intp3003.data':'$\\rm30M_{\odot}$', 'prePatton15':'$\\rm15M_{\odot}$', 'prePatton30':'$\\rm30M_{\odot}$'}
        self.LABEL_method = {0:'sliding-window', 1:'bayesian-block'}
        self.LABEL_mo = {0:'IO', 1:'NO'}
        pass

    def setMonitors(self, themonitors):
        self.monitors = themonitors
        self.monitor = themonitors[0]
        pass

    def saveFigs(self):
        for thisfigName, thisfig in self.figs.items():
            thisfig[0].savefig('/junofs/users/huangx/myProject/CCSNMonitor/figures2/online-'+self.monitor.par.sntype+'/'+thisfigName+'.eps')
            thisfig[0].savefig('/junofs/users/huangx/myProject/CCSNMonitor/figures2/online-'+self.monitor.par.sntype+'/'+thisfigName+'.svg')
            #thisfig[0].savefig('/afs/ihep.ac.cn/users/h/huangx/cmpfig/'+thisfigName+'.eps')
            #thisfig[0].savefig('/afs/ihep.ac.cn/users/h/huangx/cmpfig/'+thisfigName+'.svg')
            #thisfig[0].savefig('/junofs/users/huangx/myProject/CCSNMonitor/figures2/online-presn/'+thisfigName+'.eps')
            #thisfig[0].savefig('/junofs/users/huangx/myProject/CCSNMonitor/figures2/online-presn/'+thisfigName+'.svg')

    def draw_paper(self, figName):
        # = Draw the alert efficiency and alert time vs. distance for paper =
        # = self.monitors[0]: for FAR=1/month =
        # = self.monitors[1]: for FAR=1/year =

        # = First, define the canvas =
        fig_width = 12
        fig_height = 9
        fig_wspace = 0.02
        fig_hspace = 0
        fig = plt.figure(tight_layout=False, figsize=(fig_width*2/0.8, fig_height*2))
        #fig.subplots_adjust(top=0.9)
        gs = fig.add_gridspec(2, 2, width_ratios=(1, 1), height_ratios=(1, 1), left=0.1, right=0.9, bottom=0.05, top=0.9, wspace=fig_wspace, hspace=fig_hspace) #
        axes = {}
        tmpax00 = fig.add_subplot(gs[0, 0])
        tmpax01 = fig.add_subplot(gs[1, 0], sharex=tmpax00)
        axes[self.monitors[0].par.far] = [tmpax00, tmpax01]
        tmpax10 = fig.add_subplot(gs[0, 1], sharey=tmpax00)
        tmpax11 = fig.add_subplot(gs[1, 1], sharex=tmpax10, sharey=tmpax01)
        axes[self.monitors[1].par.far] = [tmpax10, tmpax11]
        self.figs[figName] = (fig, axes)

        # = Then, draw the curves =
        handle_legend = {'Patton':[]}
        label_legend = {'Patton':[]}
        for ii in range(0, 2):
            themonitor = self.monitors[ii]
            for model in ['prePatton15', 'prePatton30']:
                for mo in [0, 1]:
                    ldist = themonitor.getDist((model, mo))
                    #------------drawing parameters----------
                    if themonitor.par.sntype == 'sn':
                        lstyle = self.LINESTYLE_model[model]
                        lcolor = self.COLOR_mo[mo]
                        lmarker = self.MARKER_model[model]
                    elif themonitor.par.sntype == 'presn':
                        lstyle = self.LINESTYLE_mo[mo]
                        lcolor = self.COLOR_model[model]
                        lmarker = self.MARKER_model[model]

                    # = Draw the alert efficiency curve =
                    rfunc = themonitor.fit_eff((model, mo))
                    #------------draw the fit curve---------------
                    fit_x = np.linspace(ldist[0], ldist[-1]+0.5, 200)
                    fit_y = rfunc(fit_x)
                    tmp, = axes[themonitor.par.far][0].plot(fit_x, fit_y, linestyle=lstyle, color=lcolor, lw=5)
                    if ii == 0:
                        handle_legend[self.LABEL_model[model]].append(tmp)
                        label_legend[self.LABEL_model[model]].append('%s %s, %s'%(self.LABEL_model[model], self.LABEL_mass[model], self.LABEL_mo[mo]))

                    # = Draw the alert time curve =
                    # = For pre-sn =
                    ltime, ltime_err = themonitor.getTime((model, mo))
                    ltime = np.array(ltime)
                    ltime = (1./3600.)*ltime
                    ltime_err = np.array(ltime_err)
                    ltime_err = (1./3600.)*ltime_err
                    #not to draw all the points
                    idx=0
                    leff, leff_err = themonitor.getEff((model, mo))
                    for ith in range(0, len(ldist)):
                        if leff[ith]<0.55:# or alertTime[ith]>0.5
                            idx=ith-1
                            break
                    #--------------draw the original curve---------------
                    #axes[themonitor.par.far][1].errorbar(ldist[:idx+1], ltime[:idx+1], yerr=ltime_err[:idx+1], linestyle=lstyle, color=lcolor, marker=lmarker, ms=15, lw=3, capsize=5, capthick=3)
                    #axes[themonitor.par.far][1].plot(ldist[:idx+1], ltime[:idx+1], linestyle=lstyle, color=lcolor, marker=lmarker, ms=15, lw=3)
                    axes[themonitor.par.far][1].plot(ldist[:idx+1], ltime[:idx+1], linestyle=lstyle, color=lcolor, lw=5)
            pass
        # = Labels =
        axes[self.monitors[0].par.far][0].xaxis.set_tick_params(labelbottom=False)
        axes[self.monitors[1].par.far][0].xaxis.set_tick_params(labelbottom=False)
        axes[self.monitors[1].par.far][0].yaxis.set_tick_params(labelleft=False)
        axes[self.monitors[1].par.far][1].yaxis.set_tick_params(labelleft=False)
        #axes[self.monitors[0].par.far][1].set_yticks([0.1,0.2,0.3,0.4])
        axes[self.monitors[0].par.far][1].set_xticks([0,0.25,0.5,0.75,1,1.25,1.5,1.75])
        axes[self.monitors[0].par.far][0].set(xlim=[0, ldist[-1]], ylim=[0, 1.03])
        axes[self.monitors[1].par.far][0].set(xlim=[0, ldist[-1]])
        axes[self.monitors[0].par.far][1].set(ylim=[-250, 0], yscale='symlog')
        axes[self.monitors[0].par.far][1].set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        axes[self.monitors[1].par.far][1].set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        axes[self.monitors[0].par.far][0].set_ylabel(ylabel='Alert efficiency', y=1, ha='right')
        axes[self.monitors[0].par.far][1].set_ylabel(ylabel='Alert time [h]', y=1, ha='right')
        # = Legends =
        fig.legend(handle_legend['Patton'], label_legend['Patton'], ncol=4, loc='center', bbox_to_anchor=(0.5, 0.93), frameon=True, fontsize=30)
        #plt.gca().add_artist(tmp)
        # = Text =
        fig.text(x=0.12, y=0.46, s='$\\rm \\bf{Online\ preSN\ monitor}$\nFAR: %s'%(self.monitors[0].par.far_name), size=25)
        fig.text(x=0.53, y=0.46, s='$\\rm \\bf{Online\ preSN\ monitor}$\nFAR: %s'%(self.monitors[1].par.far_name), size=25)
        # = Grid =
        axes[self.monitors[0].par.far][0].grid(ls='--')
        axes[self.monitors[1].par.far][0].grid(ls='--')
        axes[self.monitors[0].par.far][1].grid(ls='--')
        axes[self.monitors[1].par.far][1].grid(ls='--')
        pass

    def drawEffciency_all(self, figName): #curves: [(model, mo), ...]
        import numpy as np
        if figName in self.figs.keys():
            fig, ax = self.figs[figName]
        else:
            fig, ax = plt.subplots()
            self.figs[figName] = (fig, ax)
        if self.monitor.par.sntype == 'sn':
            models = ['intp1311.data', 'intp3003.data', 'gar81123', 'gar82703']
            fig.subplots_adjust(top=0.85)
        elif self.monitor.par.sntype == 'presn':
            models = ['prePatton15', 'prePatton30']
        handle_legend = {'Nakazato':[], 'Garching':[], 'Patton':[]}
        label_legend = {'Nakazato':[], 'Garching':[], 'Patton':[]}
        for model in models:
            for mo in [0, 1]:
                ldist = self.monitor.getDist((model, mo))
                #------------drawing parameters----------
                lstyle = self.LINESTYLE_mo[mo]
                lcolor = self.COLOR_model[model]
                #--------------draw the fit curve---------------
                rfunc = self.monitor.fit_eff((model, mo))
                fit_x = np.linspace(ldist[0], ldist[-1]+0.5, 200)
                fit_y = rfunc(fit_x)
                tmp, = ax.plot(fit_x, fit_y, linestyle=lstyle, color=lcolor, lw=4)
                handle_legend[self.LABEL_model[model]].append(tmp)
                if self.monitor.par.sntype == 'sn':
                    label_legend[self.LABEL_model[model]].append('%s, %s'%(self.LABEL_mass[model], self.LABEL_mo[mo]))
                elif self.monitor.par.sntype == 'presn':
                    label_legend[self.LABEL_model[model]].append('%s %s, %s'%(self.LABEL_model[model], self.LABEL_mass[model], self.LABEL_mo[mo]))
        if self.monitor.par.sntype == 'sn':
            ax.text(x=50, y=0.15, s='$\\rm \\bf{Online\ SN\ monitor}$\nFAR: %s'%(self.monitor.par.far_name), size=25)
            tmp = ax.legend(handle_legend['Garching'], label_legend['Garching'], ncol=2, loc='center', bbox_to_anchor=(0.25, 1.1), title='Garching', frameon=True, fontsize=18)
            ax.legend(handle_legend['Nakazato'], label_legend['Nakazato'], ncol=2, loc='center', bbox_to_anchor=(0.75, 1.1), title='Nakazato', frameon=True, fontsize=18)
            plt.gca().add_artist(tmp)
            # = Draw galaxies =
            dist_galaxy = {'SMC':210*0.3066}#{'Milky way':30, 'LMC':170*0.3066, 'SMC':210*0.3066} #Unit:kpc
            ax.vlines(dist_galaxy.values(), ymin=0, ymax=1.05, linestyle='dashed', color='grey', lw=3)
            #---------------Draw the text--------
            for gname in ['SMC']:
                ax.text(x=dist_galaxy[gname], y=0.4, rotation=-90, s=gname, size=25)
        elif self.monitor.par.sntype == 'presn':
            ax.text(x=0.1, y=0.05, s='$\\rm \\bf{Online\ preSN\ monitor}$\nFAR: %s'%(self.monitor.par.far_name), size=25)
            ax.legend(handle_legend['Patton'], label_legend['Patton'], ncol=2, loc='center', bbox_to_anchor=(0.5, 1.07))
            # = Draw progenitors =
            dist_star = {'Betelgeuse':0.22, 'VV Cephei':0.599}
            ax.vlines(dist_star.values(), ymin=0, ymax=1.05, linestyle='dashed', color='grey', lw=3)
            #---------------Draw the text--------
            for gname in ['Betelgeuse', 'VV Cephei']:
                ax.text(x=dist_star[gname], y=0.4, ha='right', va='center', rotation=90, s=gname, size=25)
        #--------------the label and legend---------------
        #ax.set(xlim=[0, 2.0], ylim=[0, 1.05])
        ax.set(xlim=[0, ldist[-1]], ylim=[0, 1.05])
        #ax.set(xlim=[ldist[0]-10, ldist[-1]+10], ylim=[0, 1.05])
        ax.set_title(label='Alert effciency of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert effciency', y=1, ha='right')

    def drawEffciency(self, figName, curves=[]): #curves: [(model, mo), ...]
        import numpy as np
        if figName in self.figs.keys():
            fig, ax = self.figs[figName]
        else:
            fig, ax = plt.subplots()
            self.figs[figName] = (fig, ax)
        for thiscurve in curves:
            ldist = self.monitor.getDist(thiscurve)
            leff, leff_err = self.monitor.getEff(thiscurve)
            #------------drawing parameters----------
            if self.monitor.par.sntype == 'sn':
                lstyle = self.LINESTYLE_model[thiscurve[0]]
                lcolor = self.COLOR_mo[thiscurve[1]]
                lmarker = self.MARKER_model[thiscurve[0]]
            elif self.monitor.par.sntype == 'presn':
                lstyle = self.LINESTYLE_mo[thiscurve[1]]
                lcolor = self.COLOR_model[thiscurve[0]]
                lmarker = self.MARKER_model[thiscurve[0]]
            #------------draw the original curve------------
            ax.errorbar(ldist, leff, yerr=leff_err, linestyle='', color=lcolor, marker=lmarker, ms=0, lw=3, capsize=5, capthick=3)
            #--------------draw the fit curve---------------
            rfunc = self.monitor.fit_eff(thiscurve)
            fit_x = np.linspace(ldist[0], ldist[-1]+0.5, 200)
            fit_y = rfunc(fit_x)
            ax.plot(fit_x, fit_y, linestyle=lstyle, color=lcolor, lw=5, label='%s %s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mass[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))

        # = Draw the point from Iwan =
        if self.monitor.par.sntype == 'sn':
            cmp_x = {('gar81123', 0):[110,210,310,410], ('gar81123', 1):[110,210,310,410], ('gar82703', 0):[110,210,310,410], ('gar82703', 1):[110,210,310,410]}
            cmp_y = {('gar81123', 0):[0.99, 0.65,0.175,0.055], ('gar81123', 1):[1,0.65,0.195,0.05], ('gar82703', 0):[0.995,0.95,0.525,0.19], ('gar82703', 1):[0.995,0.97,0.54,0.235]}
        elif self.monitor.par.sntype == 'presn':
            cmp_x = {('prePatton15', 0):[0.4,0.5,0.6,0.8], ('prePatton15', 1):[0.5,0.8,1.1,1.4], ('prePatton30', 0):[0.5,0.8,1.1,1.4], ('prePatton30', 1):[1.0,1.3,1.6,1.9]}
            cmp_y = {('prePatton15', 0):[1,0.84,0.59,0.17], ('prePatton15', 1):[1,0.995,0.68,0.295], ('prePatton30', 0):[1,0.945,0.545,0.275], ('prePatton30', 1):[1,0.975,0.84,0.585]}
        for thiscurve in curves:
            if self.monitor.par.sntype == 'sn':
                lcolor = self.COLOR_mo[thiscurve[1]]
            elif self.monitor.par.sntype == 'presn':
                lcolor = self.COLOR_model[thiscurve[0]]
            ax.scatter(cmp_x[thiscurve], cmp_y[thiscurve], marker='*', color=lcolor, s=350)

        if self.monitor.par.sntype == 'sn':
            ax.text(x=350, y=0.6, s='$\\rm \\bf{Online\ SN\ monitor}$\n%s method\nFAR:%s'%(self.monitor.par.method_name, self.monitor.par.far_name), size=25)
        elif self.monitor.par.sntype == 'presn':
            ax.text(x=0.1, y=0.05, s='$\\rm \\bf{Online\ preSN\ monitor}$\n%s method\nFAR:%s'%(self.monitor.par.method_name, self.monitor.par.far_name), size=25)
        #--------------the label and legend---------------
        #ax.set(xlim=[0, 2.0], ylim=[0, 1.05])
        ax.set(xlim=[0, ldist[-1]], ylim=[0, 1.05])
        #ax.set(xlim=[ldist[0]-10, ldist[-1]+10], ylim=[0, 1.05])
        ax.set_title(label='Alert effciency of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert effciency', y=1, ha='right')
        ax.legend(ncol=2, loc='center', bbox_to_anchor=(0.5, 1.07))

    def drawEffciency_cmp(self, figName, curves=[]):
        nMethods = 3
        if len(self.monitors)!=nMethods:
            print('The monitor for sliding and bayesian-block is not set')
            return
        #self.monitor[0]: sliding window
        #self.monitor[1]: bayesian-block
        #self.monitor[2]: time-interval
        import numpy as np
        if figName in self.figs.keys():
            fig, ax = self.figs[figName]
        else:
            fig, ax = plt.subplots()
            self.figs[figName] = (fig, ax)
        for ithmonitor in range(0, nMethods):
            self.monitor = self.monitors[ithmonitor]
            self._set_fit_opt()
            for thiscurve in curves:
                ldist = self.monitor.getDist(thiscurve)
                leff, leff_err = self.monitor.getEff(thiscurve)
                #------------draw the original curve------------
                #ax.errorbar(ldist, leff, yerr=leff_err, linestyle='', color=self.LINESTYLEANDCOLOR2[(ithmonitor, thiscurve[1])][1], marker='o')
                #--------------draw the fit curve---------------
                fitfunc = self.fitEff(leff, leff_err, thiscurve)
                fit_x=np.linspace(ldist[0], ldist[-1], 200)
                fit_y=fitfunc(fit_x)
                ax.plot(fit_x, fit_y, linestyle=self.LINESTYLE_mo[thiscurve[1]], lw=5, color=self.COLOR_method[ithmonitor], label='%s, %s'%(self.monitor.par.method_name, self.LABEL_mo[thiscurve[1]]))
        if self.monitor.par.sntype == 'sn':
            ax.text(x=350, y=0.6, s='$\\rm \\bf{Online\ SN\ monitor}$\n%s model\nFAR<%s'%(self.LABEL_model[thiscurve[0]], self.monitor.par.far_name), size=25)
        elif self.monitor.par.sntype == 'presn':
            ax.text(x=0.1, y=0.05, s='$\\rm \\bf{Online\ preSN\ monitor}$\n%s model\nFAR<%s'%(self.LABEL_model[thiscurve[0]], self.monitor.par.far_name), size=25)
        #--------------the label and legend---------------
        ax.set(xlim=[0, ldist[-1]], ylim=[0, 1.05])
        ax.set_title(label='Alert effciency of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert effciency', y=1, ha='right')
        ax.legend(ncol=nMethods, loc='center', bbox_to_anchor=(0.5, 1.07), fontsize=20)
        return

    def drawTriggerTime_all(self, figName):
        import numpy as np
        if figName in self.figs.keys():
            fig, ax = self.figs[figName]
        else:
            fig, ax = plt.subplots()
            self.figs[figName] = (fig, ax)
        for model in ['prePatton15', 'prePatton30']:
            for mo in [0, 1]:
                ldist = self.monitor.getDist((model, mo))
                ltime, ltime_err = self.monitor.getTime((model, mo))
                ltime = np.array(ltime)
                ltime = (1./3600.)*ltime
                ltime_err = np.array(ltime_err)
                ltime_err = (1./3600.)*ltime_err
                leff, leff_err = self.monitor.getEff((model, mo))
                #---------drawing parameters-------
                lstyle = self.LINESTYLE_mo[mo]
                lcolor = self.COLOR_model[model]
                #not to draw all the points
                idx=0
                for ith in range(0, len(ldist)):
                    if leff[ith]<0.55:# or alertTime[ith]>0.5
                        idx=ith-1
                        break
        for thiscurve in curves:

            ax.errorbar(ldist[:idx+1], ltime[:idx+1], yerr=ltime_err[:idx+1], linestyle=lstyle, color=lcolor, marker=lmarker, ms=15, lw=3, capsize=5, capthick=3, label='%s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))
            #ax.plot(ldist[:idx+1], ltime[:idx+1], linestyle=lstyle, color=lcolor, marker=lmarker, ms=15, lw=3, label='%s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))
            #ax.plot(ldist[:idx+1], ltime[:idx+1], linestyle=lstyle, color=lcolor, label='%s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))
            #print('alert time at 0.2kpc for %s with MO:%d :%.6f+-%.6f'%(thiscurve[0], thiscurve[1], ltime[1], ltime_err[1]))
            print('alert time at 0.1kpc for %s with MO:%d :%.6f+-%.6f'%(thiscurve[0], thiscurve[1], ltime[0], ltime_err[0]))
            #print('alert time at 0.25kpc:%.6f'%((ltime[1]+ltime[2])/2.))
        #--------------the label and legend---------------
        ax.text(x=0.7, y=-100, s='$\\rm \\bf{Online\ preSN\ monitor}$\n%s method\nFAR<%s'%(self.monitor.par.method_name, self.monitor.par.far_name), size=25)
        ax.get_yaxis().get_major_formatter().set_scientific(False)
        ax.set(xlim=[0, 1.5], ylim=[-250, 0], yscale='symlog')
        ax.set_title(label='alert time of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert time [h]', y=1, ha='right')
        ax.legend(ncol=2, loc='center', bbox_to_anchor=(0.5, 1.07))

    def drawTriggerTime(self, figName, curves=[]):
        import numpy as np
        if figName in self.figs.keys():
            fig, ax = self.figs[figName]
        else:
            fig, ax = plt.subplots()
            self.figs[figName] = (fig, ax)
        for thiscurve in curves:
            ldist = self.monitor.getDist(thiscurve)
            ltime, ltime_err = self.monitor.getTime(thiscurve)
            ltime = np.array(ltime)
            ltime = (1./3600.)*ltime
            ltime_err = np.array(ltime_err)
            ltime_err = (1./3600.)*ltime_err
            leff, leff_err = self.monitor.getEff(thiscurve)
            #not to draw all the points
            idx=0
            for ith in range(0, len(ldist)):
                #if thiscurve[0]=='prePatton30' and thiscurve[1]==1:
                #    idx = len(ldist)-2
                #else:
                    if leff[ith]<0.55:# or alertTime[ith]>0.5
                        idx=ith-1
                        break
            #---------drawing parameters-------
            lstyle = self.LINESTYLE_mo[thiscurve[1]]
            lcolor = self.COLOR_model[thiscurve[0]]
            lmarker = self.MARKER_model[thiscurve[0]]
            #------------draw the original curve------------
            #ax.scatter(ldist[:idx+1], ltime[:idx+1], color=lcolor, marker='o')#, s=30
            ##--------------draw the interpolate curve---------------
            #par_s={('prePatton15', 0):(2, 5), ('prePatton15', 1):(2, 1e-2), ('prePatton30', 0):(2, 1e-3), ('prePatton30', 1):(2, 1e-3)}
            #split_idx = 0
            #from scipy.interpolate import UnivariateSpline
            ##spl1 = UnivariateSpline(ldist[:split_idx+1], ltime[:split_idx+1], k=par_s[thiscurve][0], s=par_s[thiscurve][1])
            ##xs1 = np.linspace(ldist[0], ldist[split_idx], 100)
            #spl2 = UnivariateSpline(ldist[split_idx:idx+2], ltime[split_idx:idx+2], k=par_s[thiscurve][0], s=par_s[thiscurve][1])
            #xs2 = np.linspace(ldist[split_idx], ldist[idx]+0.05, 100)
            ##print('alert time at 0.25kpc from spline:%.6f'%spl(0.25))
            #ax.plot(xs2, spl2(xs2), linestyle=lstyle, color=lcolor, lw=5, label='%s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))
            ##-----Try interpolate the -log
            #tmpldist = np.array(ldist[split_idx:idx+2])
            #tmpltime = np.array(ltime[split_idx:idx+2])
            #tmpltime = np.log(-tmpltime)
            #spl2 = UnivariateSpline(tmpldist, tmpltime, k=par_s[thiscurve][0], s=par_s[thiscurve][1])
            #xs2 = np.linspace(tmpldist[0], tmpldist[-1]+0.05, 100)
            #ax.plot(xs2, -np.exp(spl2(xs2)), linestyle=lstyle, color=lcolor, lw=5, label='%s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))

            #ax.errorbar(ldist[:idx+1], ltime[:idx+1], yerr=ltime_err[:idx+1], linestyle=lstyle, color=lcolor, marker=lmarker, ms=15, lw=3, capsize=5, capthick=3, label='%s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))
            ax.plot(ldist[:idx+1], ltime[:idx+1], linestyle=lstyle, color=lcolor, lw=5, label='%s %s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mass[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))
            #print('alert time at 0.2kpc for %s with MO:%d :%.6f+-%.6f'%(thiscurve[0], thiscurve[1], ltime[1], ltime_err[1]))
            print('alert time at 0.1kpc for %s with MO:%d :%.6f+-%.6f'%(thiscurve[0], thiscurve[1], ltime[0], ltime_err[0]))
            #print('alert time at 0.25kpc:%.6f'%((ltime[1]+ltime[2])/2.))

        ## = Draw the point from Iwan =
        #cmp_x = {('prePatton15', 0):[0.4,0.5], ('prePatton15', 1):[0.5,0.8,1.1], ('prePatton30', 0):[0.5,0.8,1.1], ('prePatton30', 1):[1.0,1.3,1.6,1.9]}
        #cmp_y = {('prePatton15', 0):[-4.9,-2.6], ('prePatton15', 1):[-15.6,-3.3,-0.22], ('prePatton30', 0):[-1.5,-0.55,-0.15], ('prePatton30', 1):[-1.1,-0.7,-0.3,-0.2]}
        #for thiscurve in curves:
        #    if self.monitor.par.sntype == 'sn':
        #        lcolor = self.COLOR_mo[thiscurve[1]]
        #    elif self.monitor.par.sntype == 'presn':
        #        lcolor = self.COLOR_model[thiscurve[0]]
        #    ax.scatter(cmp_x[thiscurve], cmp_y[thiscurve], marker='*', color=lcolor, s=350)
        #--------------the label and legend---------------
        ax.text(x=0.7, y=-100, s='$\\rm \\bf{Online\ preSN\ monitor}$\nFAR:%s'%(self.monitor.par.far_name), size=25)
        ax.get_yaxis().get_major_formatter().set_scientific(False)
        ax.set(xlim=[0, 1.5], ylim=[-250, 0], yscale='symlog')
        ax.set_title(label='alert time of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert time [h]', y=1, ha='right')
        ax.legend(ncol=2, loc='center', bbox_to_anchor=(0.5, 1.07))

    def drawTriggerTime_cmp(self, figName, curves=[]):
        nMethods = 3
        if len(self.monitors)!=nMethods:
            print('The monitor for sliding and bayesian-block is not set')
            return
        #self.monitor[0]: sliding window
        #self.monitor[1]: bayesian-block
        #self.monitor[2]: time-interval
        import numpy as np
        if figName in self.figs.keys():
            fig, ax = self.figs[figName]
        else:
            fig, ax = plt.subplots()
            self.figs[figName] = (fig, ax)
        for ithmonitor in range(0, nMethods):
            self.monitor = self.monitors[ithmonitor]
            for thiscurve in curves:
                ldist = self.monitor.getDist(thiscurve)
                ltime, ltime_err = self.monitor.getTime(thiscurve)
                ltime = np.array(ltime)
                ltime = (1./3600.)*ltime
                ltime_err = np.array(ltime_err)
                ltime_err = (1./3600.)*ltime_err
                leff, leff_err = self.monitor.getEff(thiscurve)
                #not to draw all the points
                idx=0
                for ith in range(0, len(ldist)):
                    if thiscurve[0]=='prePatton30' and thiscurve[1]==1:
                        idx = len(ldist)-2
                    else:
                        if leff[ith]<0.55:# or alertTime[ith]>0.5
                            idx=ith-1
                            break
                #print(idx)
                ##------------draw the original curve------------
                #ax.scatter(ldist[:idx+1], ltime[:idx+1], color=self.LINESTYLEANDCOLOR[thiscurve][1], marker='o')#, s=30
                ##--------------draw the interpolate curve---------------
                #par_s={('prePatton15', 0):1e-3, ('prePatton15', 1):1e-3, ('prePatton30', 0):1e-2, ('prePatton30', 1):1e-2}
                #from scipy.interpolate import UnivariateSpline
                #spl = UnivariateSpline(ldist[:idx+1], ltime[:idx+1], k=2, s=par_s[thiscurve])
                #print('alert time at 10kpc:%.6f'%spl(0.25))
                #xs=np.linspace(ldist[0], ldist[idx], 100)
                #ax.plot(xs, spl(xs), linestyle=self.LINESTYLEANDCOLOR[thiscurve][0], color=self.LINESTYLEANDCOLOR[thiscurve][1], label='%s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))
                ax.plot(ldist[:idx+1], ltime[:idx+1], linestyle=self.LINESTYLE_mo[thiscurve[1]], color=self.COLOR_method[ithmonitor], lw=5, label='%s, %s'%(self.monitor.par.method_name, self.LABEL_mo[thiscurve[1]]))
        #--------------the label and legend---------------
        ax.text(x=0.8, y=-100, s='$\\rm \\bf{Online\ preSN\ monitor}$\n%s model\nFAR<%s'%(self.LABEL_model[thiscurve[0]], self.monitor.par.far_name), size=25)
        ax.get_yaxis().get_major_formatter().set_scientific(False)
        ax.set(xlim=[0, 1.5], ylim=[-250, 0], yscale='symlog')
        ax.set_title(label='alert time of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert time [h]', y=1, ha='right')
        ax.legend(ncol=nMethods, loc='center', bbox_to_anchor=(0.5, 1.07), fontsize=20)
