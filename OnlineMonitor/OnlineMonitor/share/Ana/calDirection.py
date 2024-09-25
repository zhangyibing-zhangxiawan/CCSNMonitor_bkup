#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import uproot as up
import ROOT
import math
import numpy as np
class calDir_sn():
    def __init__(self):
        self.direction = {} #(model, mo):[]
        self.nIBD = {} #(model, mo):[]

        #For the figures
        self.x_scatter = {} #The directions of all trails
        self.y_scatter = {}
        self.x_curve = {} #The 68% confidence region curve
        self.y_curve = {}
        self.cl_theta = {}
        pass

    def printAveIBD(self):
        for key, val in self.nIBD.items():
            aveibd = np.mean(val)
            print('Average number of IBDs:%d for model %s with mass ordering %d'%(aveibd, key[0], key[1]))

    def getScatter(self, key):
        return self.x_scatter[key], self.y_scatter[key]

    def getCurve(self, key):
        return self.x_curve[key], self.y_curve[key]

    def getCLtheta(self, key):
        return self.cl_theta[key]

    def readDir(self, MODEL, MO):
        self.direction[(MODEL, MO)] = []
        self.nIBD[(MODEL, MO)] = []
        for ith in range(0, 200):
            #infilename = '/junofs/users/huangx/myProject/CCSNMonitor/OnlineMonitor/OnlineMonitor/myJob/result_SlidingWindow_36GW/sn_%s/%d/10/SlidingWindow/sT10_fT1e-1_3/toybkg0/sn_%d.root'%(MODEL, MO, ith)
            infilename = '/junofs/users/huangx/myProject/CCSNMonitor/OnlineMonitor/OnlineMonitor/myJob/result/sn_%s/%d/10/SlidingWindow/sT10_fT1e-1_3/toybkg0/sn_%d.root'%(MODEL, MO, ith)
            with up.open(infilename) as infile:
                sntree = infile['Event']['SN']['SNEvent']
                dirpx = sntree['f_pVertexX'].array(library='np')
                dirdx = sntree['f_dVertexX'].array(library='np')
                dirpy = sntree['f_pVertexY'].array(library='np')
                dirdy = sntree['f_dVertexY'].array(library='np')
                dirpz = sntree['f_pVertexZ'].array(library='np')
                dirdz = sntree['f_dVertexZ'].array(library='np')
                dirx = dirdx-dirpx
                diry = dirdy-dirpy
                dirz = dirdz-dirpz

                totIBDs = len(dirx)
                vdir = ROOT.TVector3(0,0,0)
                for jth in range(0, totIBDs):
                    vdir+=ROOT.TVector3(dirx[jth], diry[jth], dirz[jth]).Unit()
                vdir.RotateY(math.pi/2.)
                self.nIBD[(MODEL, MO)].append(totIBDs)
                self.direction[(MODEL, MO)].append(vdir)

    def calDirCurve(self):
        for key, val in self.direction.items():
            self.x_scatter[key] = []
            self.y_scatter[key] = []
            self.x_curve[key] = []
            self.y_curve[key] = []
            angles = []
            theta_cl = 0
            for v3 in val:
                self.x_scatter[key].append(v3.Phi())
                self.y_scatter[key].append(0.5*math.pi-v3.Theta())
                tmpangle = v3.Angle(ROOT.TVector3(1,0,0))
                angles.append(tmpangle)
            angles.sort()
            theta_cl = angles[int(0.68*len(angles))-1]
            self.cl_theta[key] = theta_cl

            vCurvePoint = []
            CL_phi=np.linspace(-math.pi, math.pi, 100)
            for phi in CL_phi:
                tmpv=ROOT.TVector3(1, 0, 0)
                tmpv.SetTheta(theta_cl)
                tmpv.SetPhi(phi)
                tmpv.RotateY(math.pi/2.)
                vCurvePoint.append(tmpv)
            for v3 in vCurvePoint:
                self.x_curve[key].append(v3.Phi())
                self.y_curve[key].append(0.5*math.pi-v3.Theta())
        pass
    pass

def drawDir(sndir):
    import matplotlib.pyplot as plt
    plt.style.use('HXStyle')
    COLORS=[]
    for color in plt.rcParams['axes.prop_cycle']:
        COLORS.append(color['color'])
    scatterColor={0:COLORS[0], 1:COLORS[6]}
    MO={0:'IO', 1:'NO'}

    fig_dir=plt.figure(figsize=[12, 9])
    axes_dir=fig_dir.add_subplot(111, projection='hammer')
    axes_dir.set(title='68% CL region')

    key0 = ('intp1311.data', 0)
    key1 = ('intp1311.data', 1)
    keys = [key0, key1]
    for key in keys:
        x_curve, y_curve = sndir.getCurve(key)
        theta_cl = sndir.getCLtheta(key)
        axes_dir.fill(x_curve, y_curve, alpha=0.3, label='%s:%.1f' % (MO[key[1]], theta_cl*180/math.pi), color=scatterColor[key[1]])
        x_scatter, y_scatter = sndir.getScatter(key)
        axes_dir.scatter(x_scatter, y_scatter, s=15, c=scatterColor[key[1]])
    axes_dir.grid()
    axes_dir.legend(loc='upper right')

    plt.show()

if __name__ == '__main__':
    dircal = calDir_sn()
    dircal.readDir('intp1311.data', 0)
    dircal.readDir('intp1311.data', 1)
    dircal.calDirCurve()
    dircal.printAveIBD()
    drawDir(dircal)
