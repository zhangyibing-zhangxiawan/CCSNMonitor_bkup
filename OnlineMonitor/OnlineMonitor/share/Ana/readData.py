#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import sys
import os
import uproot as up
import numpy as np

def get_parser():
    import argparse
    parser=argparse.ArgumentParser(description='run the drawing extraction')
    parser.add_argument('--sntype', default='presn', choices=['sn', 'presn'])
    parser.add_argument('--alertMethod', default='SlidingWindow', choices=['SlidingWindow', 'TimeInterval', 'BayesianBlock'])
    parser.add_argument('--frate', default='1permonth', choices=['1permonth', '1peryear', 'cmpSK'])
    parser.add_argument('--mo', type=int, default=0, choices=[0, 1])
    parser.add_argument('--model', help='The sn/presn model used')
    parser.add_argument('--dist', type=float, help='The distance of sn/presn')
    #parser.add_argument('--effortime', default='eff', choices=['eff', 'time'], help='The distance of sn/presn')

    return parser

class readData():
    def __init__(self, sntype):
        self.setSnType(sntype)
        self.topdir = ''
        pass

    def setSnType(self, sntype): #including whether to use toy bkg
        if sntype not in ['sn', 'presn']:
            print('Unknow sn type!')
            sys.exit()
        self.sntype = sntype

    def setTopDir(self, topdir):
        if not os.path.exists(topdir):
            print('Directory does not exist!')
            sys.exit()
        self.topdir = topdir
    
    def readData(self):
        if self.sntype=='sn':
            self.readSN()
        elif self.sntype=='presn':
            #self.readPreSN()
            self.readPreSN2()
        else:
            print('Error: Unknow type')
            sys.exit()

    def readSN(self):
        ##----------------Reading the alert time---------------
        #thetime = []
        #for ith in range(0, 200):
        #    infilename = self.topdir + '/user_sn_%d.root'%ith
        #    if not os.path.isfile(infilename):
        #        print('Warning: File does not exist: %s'%infilename)
        #        continue
        #    with up.open(infilename) as infile:
        #        alertTree = infile['alert_sn']
        #        readin = alertTree.arrays(library='np')
        #        if len(readin['alertStatus'])>2:
        #            print('Error: Unknow behavior for the %dth trail'%ith)
        #            sys.exit()
        #        if len(readin['alertStatus'])>0:
        #            tmptime = readin['alertTime'][0]
        #            thetime.append([tmptime])
        #        else:
        #            thetime.append([])
        ##------------------Store the alert time----------------
        #outfilename = self.topdir + '/times.txt'
        #print(outfilename)
        #with open(outfilename, 'wb') as outfile:
        #    for tith in thetime:
        #        np.savetxt(outfile, [tith])
        #----------------Reading and reconstruct the direction---------------
        import ROOT
        theDir = []
        thenIBD = []
        for ith in range(0, 200):
            infilename = self.topdir + '/sn_%d.root'%ith
            if not os.path.isfile(infilename):
                print('Warning: File does not exist: %s'%infilename)
                continue
            with up.open(infilename) as infile:
                if 'Event/SN;1' not in infile.keys(): continue
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

                nIBD = len(dirx)
                vdir = ROOT.TVector3(0, 0, 0)
                for jth in range(0, nIBD):
                    vdir += ROOT.TVector3(dirx[jth], diry[jth], dirz[jth]).Unit()
                thenIBD.append(nIBD)
                theDir.append(vdir)
        #------------------Store the direction----------------
        from array import array
        outfilename = self.topdir + '/sn_dir.root'
        print(outfilename)
        outfile = ROOT.TFile.Open(outfilename, 'RECREATE')
        tree_dir = ROOT.TTree('dir', 'Reconstructed directions of SN')
        dir_nIBD = array('I', [0])
        dir_x = array('d', [0.])
        dir_y = array('d', [0.])
        dir_z = array('d', [0.])
        tree_dir.Branch('nIBD', dir_nIBD, 'nIBD/I')
        tree_dir.Branch('dirx', dir_x, 'dirx/D')
        tree_dir.Branch('diry', dir_y, 'diry/D')
        tree_dir.Branch('dirz', dir_z, 'dirz/D')
        for ii in range(0, len(theDir)):
            dir_nIBD[0] = thenIBD[ii]
            dir_x[0] = theDir[ii].X()
            dir_y[0] = theDir[ii].Y()
            dir_z[0] = theDir[ii].Z()
            tree_dir.Fill()
        tree_dir.Write()
        pass

    def readPreSN(self):
        thetime = []
        #------------------Read the alert time----------------
        for ith in range(0, 200):
            infilename = self.topdir + '/eff/%dth/user_presn.root'%ith
            if os.path.isfile(infilename):
                print('Reading %s'%infilename, flush=True)
            else:
                print('%s does not exist!'%infilename, flush=True)
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
                thetime.append(time_ith)
        #------------------Store the alert time----------------
        outfilename = self.topdir + '/times.txt'
        print(outfilename)
        with open(outfilename, 'wb') as outfile:
            for tith in thetime:
                np.savetxt(outfile, [tith])
    pass

    def readPreSN2(self):
        thetime = []
        #------------------Read the alert time----------------
        for ith in range(0, 200):
            time_ith = [] #len==100
            for jth in range(1, 101):
                infilename_eff = self.topdir + '/eff/%dth/user_presn_%d.root'%(ith, jth)
                infilename_time = self.topdir + '/time/%dth/user_presn_%d.root'%(ith, jth)
                if os.path.isfile(infilename_eff) and os.path.isfile(infilename_time):
                    print('Reading %s'%infilename_eff, flush=True)
                else:
                    print('%s does not exist!'%infilename_eff, flush=True)
                    sys.exit()
                # = Read alert time according to infile_eff =
                #with up.open(infilename_eff) as infile_eff:
                #    alertTree = infile_eff['alert_presn']
                #    readin = alertTree.arrays(library='np')
                #    totalert = len(readin['alertStatus'])
                #    if totalert == 0: continue
                #    elif totalert>1:
                #        print('Error: Unknow behavior for the %dth_%d trail'%(ith, jth))
                #        sys.exit()
                #    if readin['alertStatus'][0]==1:
                #        #Open the infilename_time to read the alert time
                #        with up.open(infilename_time) as infile_time:
                #            alertTree2 = infile_time['alert_presn']
                #            readin2 = alertTree2.arrays(library='np')
                #            totalert2 = len(readin2['alertStatus'])
                #            if totalert2 == 0:
                #                #no alert in infilename_time, use the time in infilename_eff instead
                #                time_ith.append(readin['alertTime'][0])
                #            elif totalert2 == 1 and readin2['alertStatus'][0] == 1:
                #                time_ith.append(readin2['alertTime'][0])
                #            else:
                #                print('Error: Unknow behavior for alert time in %dth_%d trail'%(ith, jth))
                #                sys.exit()
                #    else:
                #        print('Error: Unknow alert status for the %dth_%d trail'%(ith, jth))
                #        sys.exit()
                # = Read alert time according to infile_time
                with up.open(infilename_time) as infile_time:
                    alertTree = infile_time['alert_presn']
                    readin = alertTree.arrays(library='np')
                    totalert = len(readin['alertStatus'])
                    if totalert == 0: continue
                    elif totalert>1:
                        print('Error: Unknow behavior for the %dth_%d trail'%(ith, jth))
                        sys.exit()
                    if readin['alertStatus'][0]==1:
                        time_ith.append(readin['alertTime'][0])
                    else:
                        print('Error: Unknow alert status for the %dth_%d trail'%(ith, jth))
                        sys.exit()
            thetime.append(time_ith)
        #------------------Store the alert time----------------
        outfilename = self.topdir + '/times.txt'
        print(outfilename)
        with open(outfilename, 'wb') as outfile:
            for tith in thetime:
                np.savetxt(outfile, [tith])

        ##----------------Reading and reconstruct the direction---------------
        #import ROOT
        #thenIBD = []
        #for ith in range(0, 200):
        #    infilename = self.topdir + '/eff/%dth/presn_nonEDM.root'%ith
        #    if os.path.isfile(infilename):
        #        print('Reading %s'%infilename, flush=True)
        #    else:
        #        print('%s does not exist!'%infilename, flush=True)
        #        continue
        #    with up.open(infilename) as infile:
        #        sntree = infile['evt']
        #        dirt = sntree['t'].array(library='np')
        #        totnIBD = 0
        #        for thist in dirt:
        #            if thist<-24.*3600: continue
        #            totnIBD += 1
        #        thenIBD.append(totnIBD)
        ##------------------Store the direction----------------
        #from array import array
        #outfilename = self.topdir + '/presn_dir.root'
        #print(outfilename)
        #outfile = ROOT.TFile.Open(outfilename, 'RECREATE')
        #tree_dir = ROOT.TTree('dir', 'Reconstructed directions of preSN')
        #dir_nIBD = array('I', [0])
        #tree_dir.Branch('nIBD', dir_nIBD, 'nIBD/I')
        #for ii in range(0, len(thenIBD)):
        #    dir_nIBD[0] = thenIBD[ii]
        #    tree_dir.Fill()
        #tree_dir.Write()
    pass

def topdir(args):
    from onlineMonitor import par_slidingWindow
    from onlineMonitor import par_timeInterval
    from onlineMonitor import par_bayesianBlock
    topdir = '/junofs/users/huangx/myProject/CCSNMonitor/OnlineMonitor/OnlineMonitor/myJob'
    if args.sntype == 'sn':
        topdir += '/result/sn_%s/%d/%d/%s'%(args.model, args.mo, args.dist, args.alertMethod)
    elif args.sntype == 'presn':
        topdir += '/result/presn_%s/%d/%.1f/%s'%(args.model, args.mo, args.dist, args.alertMethod)
    thepar = None
    if args.alertMethod == 'SlidingWindow':
        thepar = par_slidingWindow(args.sntype, args.frate)
        topdir += '/sT%d_fT%s_%d'%(thepar.T, thepar.dT, thepar.Nthr)
    elif args.alertMethod == 'TimeInterval':
        thepar = par_timeInterval(args.sntype, args.frate)
        if thepar.sntype == 'sn':
            topdir += '/%d_T%.1f'%(thepar.Nthr, thepar.T)
        elif thepar.sntype == 'presn':
            topdir += '/%d_T%d'%(thepar.Nthr, thepar.T)
    elif args.alertMethod == 'BayesianBlock':
        thepar = par_bayesianBlock(args.sntype, args.frate)
        topdir += '/ncp%.1f'%thepar.ncp_prior
    topdir += '/toybkg%d'%thepar.toybkg
    return topdir

if __name__ == '__main__':
    parser=get_parser()
    args=parser.parse_args()

    #-----------------Set the top directory-----------------
    topdir = topdir(args)
    print(topdir)

    thereader = readData(args.sntype)
    thereader.setTopDir(topdir)
    thereader.readData()
