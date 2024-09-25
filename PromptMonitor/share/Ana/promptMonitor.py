#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import sys
import numpy as np

class par():
    def __init__(self, method, far):
        self.methods = ['sliding-window', 'time-interval', 'bayesian-block']
        self.method_names = {'sliding-window':'Sliding window', 'time-interval':'Sliding event', 'bayesian-block':'Bayesian blocks'}
        self.fars = ['1permonth', '1peryear']
        self.far_names = {'1permonth':'1/month', '1peryear':'1/year'}
        self._setMethod(method)
        self._setFAR(far)
        pass

    def _setMethod(self, method):
        if method not in self.methods:
            print('Unknow alert method!')
            sys.exit()
        self.method = method
        self.method_name = self.method_names[method]
        pass

    def _setFAR(self, far):
        if far not in self.fars:
            print('Unknow false alert rate!')
            sys.exit()
        self.far = far
        self.far_name = self.far_names[far]
        pass
    pass

class par_slidingWindow(par):
    def __init__(self, far):
        super().__init__('sliding-window', far)
        self.T = 4
        self.dT = '1e-3'
        self.Nthr = 0
        if self.far == '1permonth':
            self.Nthr = 2
        elif self.far == '1peryear':
            self.Nthr = 3
        pass
    pass

class par_timeInterval(par):
    def __init__(self, far):
        super().__init__('time-interval', far)
        self.Nthr = 2
        self.T = 0
        if self.far == '1permonth':
            self.T = 7.5 #8.2
        elif self.far == '1peryear':
            self.T = 2.1 #2.4
        pass
    pass

class par_bayesianBlock(par):
    def __init__(self, far):
        super().__init__('bayesian-block', far)
        self.ncp_prior = 0
        self.Nthr = 0 #for the parameter of fit function
        if self.far == '1permonth':
            self.ncp_prior = 9.1 #9.0
            self.Nthr = 2
        elif self.far == '1peryear':
            self.ncp_prior = 11.8 #11.7
            self.Nthr = 3
        pass
    pass

class promptMonitor():
    def __init__(self):
        import numpy as np
        self.dist = np.arange(10, 500, 20)
        #The parameters of alert methods
        self.par = None

        self.trigTime = {} #(model, mo):[[], [], ..]
        self.eff = {} #(model, mo):[]
        self.eff_err = {} #(model, mo):[]
        self.time = {} #(model, mo):[]
        self.time_err = {} #(model, mo):[]

    def getNthr(self):
        if self.par.method not in ['sliding-window', 'time-interval', 'bayesian-block']:
            return 0
        return self.par.Nthr

    def getDist(self):
        return self.dist

    def getEff(self, key):
        if key in self.eff.keys():
            return self.eff[key], self.eff_err[key]
        else:
            print('Warning: key doesnot exist:', end='')
            print(key)
            return [], []

    def getTime(self, key):
        if key in self.time.keys():
            return self.time[key], self.time_err[key]
        else:
            print('Warning: key doesnot exist:', end='')
            print(key)
            return [], []

    def setPar(self, thepar):
        if not isinstance(thepar, par):
            print('Not a legal parameter!')
            sys.exit()
        self.par = thepar
        pass

    def readPromptResult(self, MODEL, MO):
        #should set the monitor parameters first
        print('Reading the data for %s with MO:%d'%(MODEL, MO))
        topDir = '/junofs/users/huangx/myProject/CCSNMonitor/PromptMonitor/myJob/result'
        import uproot as up
        self.trigTime[(MODEL, MO)] = []
        if self.par.method == 'sliding-window':
            for dist in self.dist:
                indir = topDir + '/sn_%s/%d/%d/%s/sT%d_fT%s_%d'%(MODEL, MO, dist, 'SlidingWindow', self.par.T, self.par.dT, self.par.Nthr)
                with up.open(indir+'/promptMonitor.root') as infile:
                    trigTree = infile['ttrig']
                    readin = trigTree.arrays(library='np')
                    self.trigTime[(MODEL, MO)].append(list(readin['snTriggerTime']))
        elif self.par.method == 'time-interval':
            for dist in self.dist:
                indir = topDir + '/sn_%s/%d/%d/%s/%d_T%.1f'%(MODEL, MO, dist, 'TimeInterval', self.par.Nthr, self.par.T)
                with up.open(indir+'/promptMonitor.root') as infile:
                    trigTree = infile['ttrig']
                    readin = trigTree.arrays(library='np')
                    self.trigTime[(MODEL, MO)].append(list(readin['snTriggerTime']))
        elif self.par.method == 'bayesian-block':
            for dist in self.dist:
                indir = topDir + '/sn_%s/%d/%d/%s/ncp%.1f'%(MODEL, MO, dist, 'BayesianBlock', self.par.ncp_prior)
                with up.open(indir+'/promptMonitor.root') as infile:
                    trigTree = infile['ttrig']
                    readin = trigTree.arrays(library='np')
                    self.trigTime[(MODEL, MO)].append(list(readin['snTriggerTime']))

    def calEff(self):
        import math
        totTrail = 200.
        for key, value in self.trigTime.items():
            self.eff[key] = []
            self.eff_err[key] = []
            for times in value:
                thiseff = len(times)/totTrail
                thiserr = math.sqrt(thiseff*(1-thiseff)/float(totTrail))
                if thiserr == 0:
                    thiserr = 1./200.
                self.eff[key].append(thiseff)
                self.eff_err[key].append(thiserr)
        #print(self.eff)
        #print(self.eff_err)

    def fit_eff(self, key):
        # = Fit the efficiency curve =
        print('Fitting the efficiency curve: (%s, %d)...'%(key[0],key[1]))
        def fitfunc(x, A):
            from scipy.stats import poisson
            mu=A/(x**2)
            prob=poisson.sf(self.par.Nthr, mu)
            return prob
        from scipy.optimize import curve_fit
        popt, pcov = curve_fit(fitfunc, self.dist, self.eff[key], sigma=self.eff_err[key], p0=(2e5), absolute_sigma=True)
        print('Best fit value:%d'%popt[0], end='')
        rfunc = lambda x : fitfunc(x, popt[0])
        r=np.array(self.eff[key])-rfunc(self.dist)
        chi_square=np.sum((r/np.array(self.eff_err[key]))**2)
        print('    chi square:%.2f'%chi_square)

        # = Calculate the alert distance =
        if False:
            def calDist(thefunc):
                from scipy.optimize import root_scalar
                rootfunc = lambda x : thefunc(x)-0.5
                sol = root_scalar(rootfunc, bracket=[0.1, 500], method='brentq')
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
            disterr = np.sqrt(np.var(tmpdist))
            print('Alert efficiency reach 50%% at %.1f+-%.2fkpc'%(solroot, disterr))
        return rfunc

    def calTime(self):
        import numpy as np
        for key, value in self.trigTime.items():
            self.time[key] = []
            self.time_err[key] = []
            for times in value:
                thetimes = np.array(times)
                thetimes.sort()
                orderStatistics = 0
                if len(thetimes)==0:
                    print('Warn: the length of times is 0')
                    continue
                p_cl = 0.68
                N = len(thetimes)
                orderStatistics = thetimes[int(N*p_cl)]
                def func_pdf(x):
                    cont, edges = np.histogram(thetimes, bins=20, density=True)
                    bincenter = (edges[:-1]+edges[1:])/2.
                    #Find the index of bin at which x is located
                    if x<bincenter[0]: x = bincenter[0]
                    if x>bincenter[-1]: x = bincenter[-1]
                    idx = 0
                    while idx<len(bincenter):
                        if x<bincenter[idx]: break
                        idx += 1
                    idx -= 1
                    center_beg = bincenter[idx]
                    center_end = bincenter[idx+1]
                    rval = cont[idx] + (x-center_beg)*(cont[idx+1]-cont[idx])/(center_end-center_beg)
                    return rval
                if len(thetimes)<50:
                    orderStatistics_err = 0
                else:
                    thepdf = func_pdf(orderStatistics)
                    orderStatistics_err = np.sqrt(p_cl*(1-p_cl)/(thepdf*thepdf)/N)
                self.time[key].append(orderStatistics)
                self.time_err[key].append(orderStatistics_err)
        #print(self.time)
        #print(self.time_err)

    def fit_time(self, key, idx):
        # = Use spline fit to fit the alert time curve =
        print('Fitting the alert time curve: (%s, %d)...'%(key[0],key[1]))
        par_s={('gar82703', 0):3e-3, ('gar82703', 1):3e-3, ('gar81123', 1):3e-3, ('gar81123', 0):3e-3, ('intp1311.data', 0):3e-3, ('intp1311.data', 1):6e-4, ('intp3003.data', 0):1e-3, ('intp3003.data', 1):1e-3}
        from scipy.interpolate import UnivariateSpline
        spl = UnivariateSpline(self.dist[:idx+1], self.time[key][:idx+1], k=3, s=par_s[key])
        #print('alert time at 10kpc for %s with MO:%d:%.6f'%(thiscurve[0], thiscurve[1], spl(10)))
        print('alert time at 10kpc:%.6f+-%.6f'%(self.time[key][0], self.time_err[key][0]))
        return spl

    def timePDF(self, curve):
        import matplotlib.pyplot as plt
        plt.style.use('HXStyle')

        value = self.trigTime[curve]
        ith = 0
        for times in value:
            fig, ax = plt.subplots()
            ax.set(title='dist=%dkpc'%(10+20*ith))
            ax.hist(times, bins=20, histtype='step', density=True) #, range=[-1.5e5, 0]
            ith += 1
            if ith>2: break
            #if len(times)<100: break
        plt.show()
        pass

import matplotlib.pyplot as plt
plt.style.use('HXStyle')
#COLORS=[]
#for color in plt.rcParams['axes.prop_cycle']:
#    COLORS.append(color['color'])

class promptMonitor_draw():
    def __init__(self):
        self.monitor = []

        self.figs = {} #figName: (fig, ax)
        #drawing settings
        COLORS = ['#1f77b4', '#d62728', '#ff7f0e', '#9467bd']
        self.COLOR_model = {'intp1311.data':COLORS[0], 'intp3003.data':COLORS[1], 'gar81123':COLORS[2], 'gar82703':COLORS[3]}
        self.COLOR_mo = {0:COLORS[0], 1:COLORS[1]}
        self.COLOR_method = [COLORS[0], COLORS[1], COLORS[2]]
        self.LINESTYLE_model = {'gar81123':'dashed', 'gar82703':'solid', 'intp1311.data':'dashed', 'intp3003.data':'solid'}
        self.LINESTYLE_mo = {0:'dashed', 1:'solid'}
        self.LABEL_model = {'intp1311.data':'Nakazato', 'intp3003.data':'Nakazato', 'gar81123':'Garching', 'gar82703':'Garching'}
        self.LABEL_mass = {'intp1311.data':'$\\rm13M_{\odot}$', 'intp3003.data':'$\\rm30M_{\odot}$', 'gar81123':'$\\rm11M_{\odot}$', 'gar82703':'$\\rm27M_{\odot}$'}
        self.LABEL_mo = {0:'IO', 1:'NO'}
        self.MARKER_model = {'gar81123':'.', 'gar82703':'*', 'intp1311.data':'.', 'intp3003.data':'*'}
        #self.LABEL_method = ['sliding-window', 'bayesian-block']

    def saveFigs(self):
        for thisfigName, thisfig in self.figs.items():
            thisfig[0].savefig('/junofs/users/huangx/myProject/CCSNMonitor/figures2/prompt/'+thisfigName+'.eps')
            thisfig[0].savefig('/junofs/users/huangx/myProject/CCSNMonitor/figures2/prompt/'+thisfigName+'.svg')
            #thisfig[0].savefig('/afs/ihep.ac.cn/users/h/huangx/cmpfig/'+thisfigName+'.eps')
            #thisfig[0].savefig('/afs/ihep.ac.cn/users/h/huangx/cmpfig/'+thisfigName+'.svg')

    def setMonitors(self, theMonitors):
        self.monitor = theMonitors

    def draw_paper(self, figName):
        # = Draw the alert efficiency and alert time vs. distance for paper =
        # = self.monitor[0]: for FAR=1/month =
        # = self.monitor[1]: for FAR=1/year =

        # = First, define the canvas =
        fig_width = 12
        fig_height = 9
        fig_wspace = 0.02
        fig_hspace = 0
        fig = plt.figure(tight_layout=False, figsize=(fig_width*2, fig_height*2))
        #fig.subplots_adjust(top=0.9)
        gs = fig.add_gridspec(2, 2, width_ratios=(1, 1), height_ratios=(1, 1), left=0.05, right=0.95, bottom=0.05, top=0.9, wspace=fig_wspace, hspace=fig_hspace) #
        axes = {}
        tmpax00 = fig.add_subplot(gs[0, 0])
        tmpax01 = fig.add_subplot(gs[1, 0], sharex=tmpax00)
        axes[self.monitor[0].par.far] = [tmpax00, tmpax01]
        tmpax10 = fig.add_subplot(gs[0, 1], sharey=tmpax00)
        tmpax11 = fig.add_subplot(gs[1, 1], sharex=tmpax10, sharey=tmpax01)
        axes[self.monitor[1].par.far] = [tmpax10, tmpax11]
        self.figs[figName] = (fig, axes)

        # = Then, draw the curves =
        handle_legend = {'Nakazato':[], 'Garching':[]}
        label_legend = {'Nakazato':[], 'Garching':[]}
        for ii in range(0, 2):
            themonitor = self.monitor[ii]
            ldist = themonitor.getDist()
            for model in ['intp1311.data', 'intp3003.data', 'gar81123', 'gar82703']:
                for mo in [0, 1]:
                    #------------drawing parameters----------
                    lstyle = self.LINESTYLE_mo[mo]
                    lcolor = self.COLOR_model[model]

                    # = Draw the alert efficiency curve =
                    rfunc = themonitor.fit_eff((model, mo))
                    #------------draw the fit curve---------------
                    fit_x = np.linspace(ldist[0], ldist[-1]+10, 200)
                    fit_y = rfunc(fit_x)
                    tmp, = axes[themonitor.par.far][0].plot(fit_x, fit_y, linestyle=lstyle, color=lcolor, lw=4)
                    if ii == 0:
                        handle_legend[self.LABEL_model[model]].append(tmp)
                        label_legend[self.LABEL_model[model]].append('%s, %s'%(self.LABEL_mass[model], self.LABEL_mo[mo]))

                    # = Draw the alert time curve =
                    #not to draw all the points
                    idx=0
                    leff, leff_err = themonitor.getEff((model, mo))
                    for ith in range(0, len(ldist)):
                        if leff[ith]<0.55:# or alertTime[ith]>0.5
                            idx=ith-1
                            break
                    if idx>16: #distance should be less than 300kpc
                        idx = 16
                    ##--------------draw the original curve---------------
                    #ltime, ltime_err = themonitor.getTime((model, mo))
                    #axes[themonitor.par.far][1].plot(ldist[:idx], ltime[:idx], linestyle=lstyle, color=lcolor, lw=4)
                    #--------------draw the interpolate curve---------------
                    spl = themonitor.fit_time((model, mo), idx)
                    xs = np.linspace(ldist[0], ldist[idx], 100)
                    axes[themonitor.par.far][1].plot(xs, spl(xs), linestyle=lstyle, color=lcolor, lw=4)
            pass
        # = Labels =
        axes[self.monitor[0].par.far][0].xaxis.set_tick_params(labelbottom=False)
        axes[self.monitor[1].par.far][0].xaxis.set_tick_params(labelbottom=False)
        axes[self.monitor[1].par.far][0].yaxis.set_tick_params(labelleft=False)
        axes[self.monitor[1].par.far][1].yaxis.set_tick_params(labelleft=False)
        axes[self.monitor[0].par.far][1].set_yticks([0.1,0.2,0.3,0.4])
        axes[self.monitor[0].par.far][1].set_xticks([0, 100, 200, 300, 400])
        axes[self.monitor[0].par.far][0].set(xlim=[ldist[0]-10, ldist[-1]+10], ylim=[0, 1.03])
        axes[self.monitor[1].par.far][0].set(xlim=[ldist[0]-10, ldist[-1]+10])
        axes[self.monitor[0].par.far][1].set(ylim=[0.01, 0.5])
        axes[self.monitor[0].par.far][1].set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        axes[self.monitor[1].par.far][1].set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        axes[self.monitor[0].par.far][0].set_ylabel(ylabel='Alert efficiency', y=1, ha='right')
        axes[self.monitor[0].par.far][1].set_ylabel(ylabel='Alert time [s]', y=1, ha='right')
        # = Legends =
        tmp = fig.legend(handle_legend['Nakazato'], label_legend['Nakazato'], ncol=4, loc='center', bbox_to_anchor=(0.27, 0.93), title='Nakazato', frameon=True, fontsize=21) #
        fig.legend(handle_legend['Garching'], label_legend['Garching'], ncol=4, loc='center', bbox_to_anchor=(0.73, 0.93), title='Garching', frameon=True, fontsize=21)
        plt.gca().add_artist(tmp)
        # = Text =
        fig.text(x=0.07, y=0.46, s='$\\rm \\bf{Prompt\ monitor}$\nFAR: %s'%(self.monitor[0].par.far_name), size=25)
        fig.text(x=0.53, y=0.46, s='$\\rm \\bf{Prompt\ monitor}$\nFAR: %s'%(self.monitor[1].par.far_name), size=25)
        # = Grid =
        axes[self.monitor[0].par.far][0].grid(ls='--')
        axes[self.monitor[1].par.far][0].grid(ls='--')
        axes[self.monitor[0].par.far][1].grid(ls='--')
        axes[self.monitor[1].par.far][1].grid(ls='--')
        pass

    def drawEffciency_all(self, figName, ithMonitor=0):
        themonitor = self.monitor[ithMonitor]
        import numpy as np
        fig, ax = plt.subplots()
        fig.subplots_adjust(top=0.85)
        self.figs[figName] = (fig, ax)
        ldist = themonitor.getDist()
        handle_legend = {'Nakazato':[], 'Garching':[]}
        label_legend = {'Nakazato':[], 'Garching':[]}
        #from scipy.optimize import curve_fit
        for model in ['intp1311.data', 'intp3003.data', 'gar81123', 'gar82703']:
            for mo in [0, 1]:
                rfunc = themonitor.fit_eff((model, mo))
                #------------drawing parameters----------
                lstyle = self.LINESTYLE_mo[mo]
                lcolor = self.COLOR_model[model]
                #lmarker = self.MARKER_model[model]
                #------------draw the fit curve---------------
                fit_x = np.linspace(ldist[0], ldist[-1]+10, 200)
                fit_y = rfunc(fit_x)
                tmp, = ax.plot(fit_x, fit_y, linestyle=lstyle, color=lcolor, lw=4)
                handle_legend[self.LABEL_model[model]].append(tmp)
                label_legend[self.LABEL_model[model]].append('%s, %s'%(self.LABEL_mass[model], self.LABEL_mo[mo]))

        # = Draw galaxies =
        dist_galaxy = {'SMC':210*0.3066}#{'Milky way':30, 'LMC':170*0.3066, 'SMC':210*0.3066} #Unit:kpc
        ax.vlines(dist_galaxy.values(), ymin=0, ymax=1.05, linestyle='dashed', color='grey', lw=3)
        # = Draw the text =
        for gname in ['SMC']:
            ax.text(x=dist_galaxy[gname], y=0.4, rotation=-90, s=gname, size=25)

        #--------------the label and legend---------------
        ax.text(x=30, y=0.15, s='$\\rm \\bf{Prompt\ monitor}$\nFAR: %s'%(themonitor.par.far_name), size=25)
        ax.set(xlim=[ldist[0]-10, ldist[-1]+10], ylim=[0, 1.05])
        ax.set_title(label='Alert effciency of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right') #, fontsize=23
        ax.set_ylabel(ylabel='Alert efficiency', y=1, ha='right')
        tmp = ax.legend(handle_legend['Garching'], label_legend['Garching'], ncol=2, loc='center', bbox_to_anchor=(0.25, 1.1), title='Garching', frameon=True, fontsize=18) #1.1, 0.25
        ax.legend(handle_legend['Nakazato'], label_legend['Nakazato'], ncol=2, loc='center', bbox_to_anchor=(0.75, 1.1), title='Nakazato', frameon=True, fontsize=18) #1.1, 0.75
        plt.gca().add_artist(tmp)

    def drawEffciency(self, figName, ithMonitor=0):
        themonitor = self.monitor[ithMonitor]
        import numpy as np
        fig, ax = plt.subplots()
        self.figs[figName] = (fig, ax)
        #curves = [('intp1311.data', 0), ('intp1311.data', 1), ('intp3003.data', 0), ('intp3003.data', 1)] #('gar81123', 0), ('gar82703', 1), 
        curves = [('gar81123', 0), ('gar81123', 1), ('gar82703', 0), ('gar82703', 1)] #
        #curves = [('intp1311.data', 0), ('intp1311.data', 1), ('intp3003.data', 0), ('intp3003.data', 1), ('gar81123', 0), ('gar81123', 1), ('gar82703', 0), ('gar82703', 1)] #
        ldist = themonitor.getDist()
        for thiscurve in curves:
            leff, leff_err = themonitor.getEff(thiscurve)
            #------------drawing parameters----------
            lstyle = self.LINESTYLE_model[thiscurve[0]]
            lcolor = self.COLOR_mo[thiscurve[1]]
            lmarker = self.MARKER_model[thiscurve[0]]
            #------------draw the original curve------------
            ax.errorbar(ldist, leff, yerr=leff_err, linestyle='', color=lcolor, marker=lmarker, ms=0, lw=3, capsize=5, capthick=3)
            #------------Fit the curve
            rfunc = themonitor.fit_eff(thiscurve)
            #------------draw the fit curve---------------
            fit_x=np.linspace(ldist[0], ldist[-1]+10, 200)
            fit_y = rfunc(fit_x)
            #fit_y=fitfunc(fit_x, popt[0])
            ax.plot(fit_x, fit_y, linestyle=lstyle, color=lcolor, lw=5, label='%s %s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mass[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))
        # = Draw the points from Iwan =
        cmp_x = {('gar81123', 0):[110, 210, 310, 410], ('gar81123', 1):[110, 210, 310, 410], ('gar82703', 0):[110, 210, 310, 410], ('gar82703', 1):[110, 210, 310, 410]}
        cmp_y = {('gar81123', 0):[1,0.615,0.175,0.05], ('gar81123', 1):[0.99,0.645,0.195,0.045], ('gar82703', 0):[0.995,0.95,0.535,0.2], ('gar82703', 1):[1,0.965,0.615,0.22]}
        for thiscurve in curves:
            lcolor = self.COLOR_mo[thiscurve[1]]
            ax.scatter(cmp_x[thiscurve], cmp_y[thiscurve], marker='*', color=lcolor, s=350)#

        #--------------the label and legend---------------
        ax.text(x=30, y=0.15, s='$\\rm \\bf{Prompt\ monitor}$\n%s method\nFAR:%s'%(themonitor.par.method_name, themonitor.par.far_name), size=25)
        ax.set(xlim=[ldist[0]-10, ldist[-1]+10], ylim=[0, 1.05])
        ax.set_title(label='Alert effciency of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right') #, fontsize=23
        ax.set_ylabel(ylabel='Alert efficiency', y=1, ha='right')
        ax.legend(ncol=2, loc='center', bbox_to_anchor=(0.5, 1.07))

    def drawTriggerTime_all(self, figName, ithMonitor=0):
        themonitor = self.monitor[ithMonitor]
        import numpy as np
        fig, ax = plt.subplots()
        fig.subplots_adjust(top=0.85)
        self.figs[figName] = (fig, ax)
        ldist = themonitor.getDist()
        handle_legend = {'Nakazato':[], 'Garching':[]}
        label_legend = {'Nakazato':[], 'Garching':[]}
        for model in ['intp1311.data', 'intp3003.data', 'gar81123', 'gar82703']:
            for mo in [0, 1]:
                ltime, ltime_err = themonitor.getTime((model, mo))
                leff, leff_err = themonitor.getEff((model, mo))
                #------------drawing parameters----------
                lstyle = self.LINESTYLE_mo[mo]
                lcolor = self.COLOR_model[model]
                #not to draw all the points
                idx=0
                for ith in range(0, len(ldist)):
                    if leff[ith]<0.55:# or alertTime[ith]>0.5
                        idx=ith-1
                        break
                if idx>16: #distance should be less than 300kpc
                    idx = 16
                ##--------------draw the interpolate curve---------------
                #par_s={('gar82703', 0):3e-3, ('gar82703', 1):3e-3, ('gar81123', 1):3e-3, ('gar81123', 0):3e-3, ('intp1311.data', 0):3e-3, ('intp1311.data', 1):6e-4, ('intp3003.data', 0):1e-3, ('intp3003.data', 1):1e-3}
                #from scipy.interpolate import UnivariateSpline
                #spl = UnivariateSpline(ldist[:idx+1], ltime[:idx+1], k=3, s=par_s[(model, mo)])
                ##print('alert time at 10kpc for %s with MO:%d:%.6f'%(thiscurve[0], thiscurve[1], spl(10)))
                ##print('alert time at 10kpc for %s with MO:%d:%.6f+-%.6f'%(thiscurve[0], thiscurve[1], ltime[0], ltime_err[0]))
                #xs=np.linspace(ldist[0], ldist[idx], 100)
                #tmp, = ax.plot(xs, spl(xs), linestyle=lstyle, color=lcolor, lw=4)
                #--------------draw the original curve---------------
                tmp, = ax.plot(ldist[:idx], ltime[:idx], linestyle=lstyle, color=lcolor, lw=4)
                handle_legend[self.LABEL_model[model]].append(tmp)
                label_legend[self.LABEL_model[model]].append('%s, %s'%(self.LABEL_mass[model], self.LABEL_mo[mo]))
        #--------------the label and legend---------------
        ax.text(x=200, y=0.1, s='$\\rm \\bf{Prompt\ monitor}$\nFAR: %s'%(themonitor.par.far_name), size=25)
        ax.get_yaxis().get_major_formatter().set_scientific(False)
        ax.set(xlim=[ldist[0]-10, ldist[-5]], ylim=[0.01, 0.5]) #
        ax.set_title(label='Alert time of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert time [s]', y=1, ha='right')
        tmp = ax.legend(handle_legend['Garching'], label_legend['Garching'], ncol=2, loc='center', bbox_to_anchor=(0.25, 1.1), title='Garching', frameon=True, fontsize=18) #1.1, 0.25
        ax.legend(handle_legend['Nakazato'], label_legend['Nakazato'], ncol=2, loc='center', bbox_to_anchor=(0.75, 1.1), title='Nakazato', frameon=True, fontsize=18) #1.1, 0.75
        plt.gca().add_artist(tmp)

    def drawTriggerTime(self, figName, ithMonitor=0):
        themonitor = self.monitor[ithMonitor]
        import numpy as np
        fig, ax = plt.subplots()
        self.figs[figName] = (fig, ax)
        #curves = [('intp1311.data', 0), ('intp1311.data', 1), ('intp3003.data', 0), ('intp3003.data', 1)] #('gar81123', 0), ('gar82703', 1), 
        curves = [('gar81123', 0), ('gar81123', 1), ('gar82703', 0), ('gar82703', 1)] #
        #curves = [('intp1311.data', 0), ('intp1311.data', 1), ('intp3003.data', 0), ('intp3003.data', 1), ('gar81123', 0), ('gar81123', 1), ('gar82703', 0), ('gar82703', 1)] #
        ldist = themonitor.getDist()
        for thiscurve in curves:
            ltime, ltime_err = themonitor.getTime(thiscurve)
            leff, leff_err = themonitor.getEff(thiscurve)
            #------------drawing parameters----------
            lstyle = self.LINESTYLE_model[thiscurve[0]]
            lcolor = self.COLOR_mo[thiscurve[1]]
            lmarker = self.MARKER_model[thiscurve[0]]
            #not to draw all the points
            idx=0
            for ith in range(0, len(ldist)):
                #if thiscurve[0]=='intp3003.data' and thiscurve[1]==0:
                #    if leff[ith]<0.55 or ltime[ith]>0.5:
                #        idx=ith-1
                #        break
                #else:
                    if leff[ith]<0.55:# or alertTime[ith]>0.5
                        idx=ith-1
                        break
            if idx>16: #distance should be less than 300kpc
                idx = 16
            #------------draw the original curve------------
            ax.errorbar(ldist[:idx+1], ltime[:idx+1], yerr=ltime_err[:idx+1], linestyle='', marker=lmarker, ms=0, color=lcolor, lw=3, capsize=5, capthick=3) #, label='%s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mo[thiscurve[1]])
            #--------------draw the interpolate curve---------------
            #par_s={('intp1311.data', 0):3e-3, ('intp1311.data', 1):3e-4, ('intp3003.data', 0):1e-3, ('intp3003.data', 1):1e-3}
            par_s={('gar82703', 0):3e-3, ('gar82703', 1):3e-3, ('gar81123', 1):3e-3, ('gar81123', 0):3e-3, ('intp1311.data', 0):3e-3, ('intp1311.data', 1):6e-4, ('intp3003.data', 0):1e-3, ('intp3003.data', 1):1e-3}
            from scipy.interpolate import UnivariateSpline
            spl = UnivariateSpline(ldist[:idx+1], ltime[:idx+1], k=3, s=par_s[thiscurve])
            #print('alert time at 10kpc for %s with MO:%d:%.6f'%(thiscurve[0], thiscurve[1], spl(10)))
            print('alert time at 10kpc for %s with MO:%d:%.6f+-%.6f'%(thiscurve[0], thiscurve[1], ltime[0], ltime_err[0]))
            xs=np.linspace(ldist[0], ldist[idx], 100)
            ax.plot(xs, spl(xs), linestyle=lstyle, color=lcolor, lw=5, label='%s %s, %s'%(self.LABEL_model[thiscurve[0]], self.LABEL_mass[thiscurve[0]], self.LABEL_mo[thiscurve[1]]))

        # = Draw the points from Iwan =
        cmp_x = {('gar81123', 0):[110, 210, 310, 410], ('gar81123', 1):[110, 210, 310, 410], ('gar82703', 0):[110, 210, 310, 410], ('gar82703', 1):[110, 190, 210, 310, 410]}
        cmp_y = {('gar81123', 0):[0.445,1.457,2.376,2.499], ('gar81123', 1):[0.434,1.629,2.300,2.440], ('gar82703', 0):[0.207,0.971,2.040,2.210], ('gar82703', 1):[0.183, 0.649,0.647,1.833,2.426]}
        for thiscurve in curves:
            lcolor = self.COLOR_mo[thiscurve[1]]
            ax.scatter(cmp_x[thiscurve], cmp_y[thiscurve], marker='*', color=lcolor, s=350)#

        ax.text(x=200, y=0.1, s='$\\rm \\bf{Prompt\ monitor}$\n%s method\nFAR:%s'%(themonitor.par.method_name, themonitor.par.far_name), size=25)
        #--------------the label and legend---------------
        ax.get_yaxis().get_major_formatter().set_scientific(False)
        ax.set(xlim=[ldist[0]-10, ldist[-5]], ylim=[0.01, 1]) #
        ax.set_title(label='Alert time of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert time [s]', y=1, ha='right')
        ax.legend(ncol=2, loc='center', bbox_to_anchor=(0.5, 1.07))

    def drawEff_cmp(self, figName):
        nMethods = 3
        if len(self.monitor)!=nMethods:
            print('The monitor for sliding and bayesian-block is not set')
            return
        #self.monitor[0]: sliding window
        #self.monitor[1]: bayesian-block
        #self.monitor[2]: time-interval
        import numpy as np
        fig, ax = plt.subplots()
        self.figs[figName] = (fig, ax)
        #curves = [('intp1311.data', 0), ('intp1311.data', 1)] #, ('intp3003.data', 0), ('intp3003.data', 1)]
        curves = [('gar82703', 0), ('gar82703', 1)] #, ('intp3003.data', 0), ('intp3003.data', 1)]
        ldist = self.monitor[0].getDist()
        for ithmonitor in range(0, nMethods):
            themonitor = self.monitor[ithmonitor]
            for thiscurve in curves:
                leff, leff_err = themonitor.getEff(thiscurve)
                #------------drawing parameters----------
                lstyle = self.LINESTYLE_mo[thiscurve[1]]
                lcolor = self.COLOR_method[ithmonitor]
                #------------draw the original curve------------
                #ax.errorbar(ldist, leff, yerr=leff_err, linestyle='', color=COLOR[ithmonitor], marker='o')#LINESTYLE[mo], ms=6
                #--------------draw the fit curve---------------
                from scipy.optimize import curve_fit
                nthr = themonitor.getNthr()
                def fitfunc(x, A):
                    from scipy.stats import poisson
                    mu=A/(x**2)
                    prob=poisson.sf(nthr, mu)
                    return prob
                popt, pcov=curve_fit(fitfunc, ldist, leff, sigma=leff_err, p0=(2e5), absolute_sigma=True)
                print('best fit value:%d'%popt[0])
                r=np.array(leff)-fitfunc(ldist, popt[0])
                chi_square=np.sum((r/np.array(leff_err))**2)
                print('chi square:%.2f'%chi_square)
                fit_x=np.linspace(ldist[0], ldist[-1]+10, 200)
                fit_y=fitfunc(fit_x, popt[0])
                ax.plot(fit_x, fit_y, linestyle=lstyle, color=lcolor, lw=5, label='%s, %s'%(themonitor.par.method_name, self.LABEL_mo[thiscurve[1]]))
        ax.text(x=30, y=0.15, s='$\\rm \\bf{Prompt\ monitor}$\n%s model\nFAR<%s'%(self.LABEL_model[curves[0][0]], themonitor.par.far_name), size=25)
        #--------------the label and legend---------------
        ax.set(xlim=[ldist[0]-10, ldist[-1]+10], ylim=[0, 1.05])
        ax.set_title(label='Alert effciency of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert effciency', y=1, ha='right')
        ax.legend(ncol=nMethods, loc='center', bbox_to_anchor=(0.5, 1.07), fontsize=20)
        return

    def drawTime_cmp(self, figName):
        nMethods = 3
        if len(self.monitor)!=nMethods:
            print('The monitor for sliding and bayesian-block is not set')
            return
        #self.monitor[0]: sliding window
        #self.monitor[1]: bayesian-block
        #self.monitor[2]: time-interval
        import numpy as np
        fig, ax = plt.subplots()
        self.figs[figName] = (fig, ax)
        #curves = [('intp1311.data', 0), ('intp1311.data', 1)] #, ('intp3003.data', 0), ('intp3003.data', 1)]
        curves = [('gar82703', 0), ('gar82703', 1)] #, ('intp3003.data', 0), ('intp3003.data', 1)]
        ldist = self.monitor[0].getDist()
        for ithmonitor in range(0, nMethods):
            themonitor = self.monitor[ithmonitor]
            for thiscurve in curves:
                ltime, ltime_err = themonitor.getTime(thiscurve)
                leff, leff_err = themonitor.getEff(thiscurve)
                #------------drawing parameters----------
                lstyle = self.LINESTYLE_mo[thiscurve[1]]
                lcolor = self.COLOR_method[ithmonitor]
                #not to draw all the points
                idx=0
                for ith in range(0, len(ldist)):
                    if thiscurve[0]=='intp3003.data' and thiscurve[1]==0:
                        if leff[ith]<0.55 or ltime[ith]>0.5:
                            idx=ith-1
                            break
                    else:
                        if leff[ith]<0.55:# or alertTime[ith]>0.5
                            idx=ith-1
                            break
                if idx>15: #distance should be less than 300kpc
                    idx = 15
                #------------draw the original curve------------
                #ax.scatter(ldist[:idx+1], ltime[:idx+1], color=COLOR[ithmonitor], marker='o')#, s=30
                #--------------draw the interpolate curve---------------
                par_s={('gar82703', 0):3e-3, ('gar82703', 1):3e-3, ('gar81123', 1):3e-3, ('gar81123', 0):3e-3, ('intp1311.data', 0):3e-3, ('intp1311.data', 1):6e-4, ('intp3003.data', 0):1e-3, ('intp3003.data', 1):1e-3}
                from scipy.interpolate import UnivariateSpline
                spl = UnivariateSpline(ldist[:idx+1], ltime[:idx+1], k=3, s=par_s[thiscurve])
                print('alert time at 10kpc:%.6f'%spl(10))
                xs=np.linspace(ldist[0], ldist[idx], 100)
                ax.plot(xs, spl(xs), linestyle=lstyle, color=lcolor, lw=5, label='%s, %s'%(themonitor.par.method_name, self.LABEL_mo[thiscurve[1]]))
        ax.text(x=200, y=0.1, s='$\\rm \\bf{Prompt\ monitor}$\n%s model\nFAR<%s'%(self.LABEL_model[curves[0][0]], themonitor.par.far_name), size=25)
        #--------------the label and legend---------------
        ax.get_yaxis().get_major_formatter().set_scientific(False)
        ax.set(xlim=[ldist[0]-10, ldist[-5]], ylim=[0.01, 0.5])
        ax.set_title(label='alert time of SN', visible=False)
        ax.set_xlabel(xlabel='Distance [kpc]', x=1, ha='right')
        ax.set_ylabel(ylabel='Alert time [s]', y=1, ha='right')
        ax.legend(ncol=nMethods, loc='center', bbox_to_anchor=(0.5, 1.07), fontsize=20)
        return
