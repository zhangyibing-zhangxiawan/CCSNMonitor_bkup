#!/usr/bin/env python
#-*- coding: utf-8 -*-

import Sniper
import os

def get_parser():
    import argparse
    parser=argparse.ArgumentParser(description='run OEC')
    parser.add_argument("--loglevel", default="Debug", 
                            choices=["Test", "Debug", "Info", "Warn", "Error", "Fatal"],
                            help="Set the Log Level")
    parser.add_argument("--evtmax", type=int, default=-1, help='events to be processed')
    parser.add_argument("--input", help="input file name")
    parser.add_argument("--inputList", action="append", help="input file list name")
    parser.add_argument("--output", help="output file name")
    parser.add_argument("--user-output", default="user-sample_oec.root", help="output file name")

    return parser

DATA_LOG_MAP = {
        "Test":0, "Debug":2, "Info":3, "Warn":4, "Error":5, "Fatal":6
        }

if __name__ == "__main__":
    parser=get_parser()
    args=parser.parse_args()

    topTask=Sniper.TopTask("TopTask")
    topTask.setLogLevel(DATA_LOG_MAP[args.loglevel])
    topTask.setEvtMax(args.evtmax)

    #----------------Input
    filelist=[]
    if args.input:
        filelist.append(args.input)
    if args.inputList:
        for fname in args.inputList:
            with open(fname) as hxf:
                for line in hxf:
                    line=line.strip()
                    filelist.append(line)
    import RootIOSvc
    import BufferMemMgr
    bufmgr=topTask.createSvc("BufferMemMgr")
    bufmgr.property("StopTaskOpt").set(1)
    #bufmgr.property("TimeWindow").set([-10,10])
    readin=topTask.createSvc("RootInputSvc/InputSvc")
    readin.property("InputFile").set(filelist)

    #----------Output
    import RootWriter
    rootwriter = topTask.createSvc("RootWriter")
    rootwriter.property("Output").set({"USER_OUTPUT":args.user_output, "USER_SN":args.user_output, "USER_PRESN":args.user_output})

    Sniper.loadDll('libreadSNEvt.so')
    readsnevtalg = topTask.createAlg("readSNEvt")

    #==============================================================================
    #RUN
    topTask.show()
    topTask.run()

