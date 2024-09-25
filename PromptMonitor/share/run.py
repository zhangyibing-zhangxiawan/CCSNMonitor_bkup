#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: huangxin

import Sniper

def get_parser():
    import argparse
    parser=argparse.ArgumentParser(description='run supernova prompt monitor')
    parser.add_argument('--loglevel', default='Debug', choices=['Test', 'Debug', 'Info', 'Warn', 'Error', 'Fatal'], help='set the log level')
    parser.add_argument('--evtmax', type=int, default=-1, help='events to be processed, do not change this value to complete the trigger for one SN burst')
    parser.add_argument("--input", action='append', help="input file name, if one SN burst is simulated in one file, use this parameter")
    parser.add_argument("--inputList", action="append", help="input file list name, if one SN burst is simulated in several files, use this parameter rather than --input")
    parser.add_argument('--output', default='sample.root', help='output file name')
    parser.add_argument('--user-output', default='user-sample.root', help='user output file name, stores the result of SN trigger')

    #set the parameters
    #-----------parameters of the PromptMonitor----------------
    parser.add_argument('--method', default='SlidingWindow', choices=['SlidingWindow', 'TimeInterval', 'BayesianBlock'], help='the length of the time window')
    #-----------parameters of the sliding window method and time interval method----------------
    #common
    parser.add_argument('--T', type=float, default=4, help='the length of the time window')
    parser.add_argument('--Nthr', type=int, default=3, help='the threshold of n to give alert')
    parser.add_argument('--startTime', type=float, default='-5', help='the threshold of n to give alert')
    #for sliding window method
    parser.add_argument('--dT', type=float, default=1e-3, help='the step of the')
    #for time interval method
    #-----------parameters of the bayesian block method tool----------------
    parser.add_argument('--ncp', type=float, default=7., help='the ncp_prior for BayesianBlock')
    return parser

DATA_LOG_MAP = {
        "Test":0, "Debug":2, "Info":3, "Warn":4, "Error":5, "Fatal":6
        }

if __name__ == '__main__':
    parser=get_parser()
    args=parser.parse_args()

    topTask=Sniper.TopTask('topTask')
    topTask.setLogLevel(DATA_LOG_MAP[args.loglevel])
    topTask.setEvtMax(args.evtmax)

    #=============for input file==================
    filelist=[]
    if args.input:
        for f in args.input:
            filelist.append(f)
    if args.inputList:
        for fname in args.inputList:
            with open(fname) as hxf:
                for line in hxf:
                    line=line.strip()
                    filelist.append(line)
    #the data buffer
    import BufferMemMgr
    bufMgr=topTask.createSvc('BufferMemMgr')
    #input svc
    import RootIOSvc
    readin=topTask.createSvc('RootInputSvc/InputSvc')
    readin.property('InputFile').set(filelist)
    #output svc
    import RootWriter
    rootwriter=topTask.createSvc("RootWriter")
    rootwriter.property("Output").set({"SN_TRIGGER":args.user_output})

    import PromptMonitor
    hwtrigger=topTask.createAlg('PromptMonitor')
    hwtrigger.property('Method').set(args.method)
    if args.method == 'SlidingWindow':
        monitortool = hwtrigger.createTool("SlidingWindow/snlike")
        monitortool.property("slideT").set(args.T)
        monitortool.property("freshT").set(args.dT)
        monitortool.property("Nthr").set(args.Nthr)
        monitortool.property("startTime").set(args.startTime)
    elif args.method == 'TimeInterval':
        monitortool = hwtrigger.createTool("TimeInterval/snlike")
        monitortool.property("T").set(args.T)
        monitortool.property("Nthr").set(args.Nthr)
        monitortool.property("startTime").set(args.startTime)
    elif args.method == 'BayesianBlock':
        monitortool = hwtrigger.createTool("BayesianBlock/snlike")
        monitortool.property("ncp_prior").set(args.ncp)

    topTask.show()
    topTask.run()
