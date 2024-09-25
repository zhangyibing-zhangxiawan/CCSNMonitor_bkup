#!/usr/bin/env python
#-*- coding: utf-8 -*-

import Sniper
import os

def get_parser():
    import argparse
    parser=argparse.ArgumentParser(description='run OEC')
    parser.add_argument("--loglevel", default="Info", 
                            choices=["Test", "Debug", "Info", "Warn", "Error", "Fatal"],
                            help="Set the Log Level")
    parser.add_argument("--evtmax", type=int, default=-1, help='events to be processed')
    parser.add_argument("--input", help="input file name")
    parser.add_argument("--inputList", action="append", help="input file list name")
    parser.add_argument("--output", help="output file name")
    parser.add_argument("--user-output", default="user-sample_oec.root", help="output file name")

    #For IBD selection
    parser.add_argument("--configFile", help="The json file contains the IBD selection criteria")

    #For toy background
    parser.add_argument("--enableSNtoybkg", dest='toybkg_sn', action='store_true')
    parser.add_argument("--disableSNtoybkg", dest='toybkg_sn', action='store_false')
    parser.set_defaults(toybkg_sn=False)
    parser.add_argument("--enablePretoybkg", dest='toybkg_pre', action='store_true')
    parser.add_argument("--disablePretoybkg", dest='toybkg_pre', action='store_false')
    parser.set_defaults(toybkg_pre=False)

    #For supernova monitor
    parser.add_argument("--monitorMethod", default="SlidingWindow", choices=["SlidingWindow", "TimeInterval", "BayesianBlock"], help="output file name")
    parser.add_argument("--enableSpecifiedStart", dest='specifiedStart', action='store_true')
    parser.add_argument("--disableSpecifiedStart", dest='specifiedStart', action='store_false')
    parser.set_defaults(specifiedStart=True)
    parser.add_argument('--beginTime', type=float, default=0, help='The time when to start the monitor')
    parser.add_argument('--seed', type=int, default=0, help='The seed for random numbers')
    #-----------parameters of the sliding window method and time interval method----------------
    #common
    parser.add_argument('--sn-T', type=float, default=10, help='the length of the time window')
    parser.add_argument('--sn-Nthr', type=int, default=3, help='the threshold of n to give alert')
    parser.add_argument('--sn-startTime', type=float, default=-5, help='the start time')
    parser.add_argument('--presn-T', type=float, default=4, help='the length of the time window')
    parser.add_argument('--presn-Nthr', type=int, default=3, help='the threshold of n to give alert')
    parser.add_argument('--presn-startTime', type=float, default=-10*24*3600, help='the start time')
    #for sliding window method
    parser.add_argument('--sn-dT', type=float, default=0.1, help='the step of the')
    parser.add_argument('--presn-dT', type=float, default=1e-3, help='the step of the')
    #for time interval method
    #-----------parameters of the bayesian block method tool----------------
    parser.add_argument('--sn-ncp', type=float, default=7., help='the ncp_prior for BayesianBlock')
    parser.add_argument('--presn-ncp', type=float, default=7., help='the ncp_prior for BayesianBlock')

    return parser

DATA_LOG_MAP = {
        "Test":0, "Debug":2, "Info":3, "Warn":4, "Error":5, "Fatal":6
        }

if __name__ == "__main__":
    parser=get_parser()
    args=parser.parse_args()

    # == Create Top Task ==
    topTask = Sniper.TopTask("TopTask")
    topTask.setLogLevel(DATA_LOG_MAP[args.loglevel])
    topTask.setEvtMax(args.evtmax)

    # == Create subTasks =
    inputTask = topTask.createTask("Task/input_Task")
    LECTask = topTask.createTask("Task/LEC_Task")
    HECTask = topTask.createTask("Task/HEC_Task")
    outputTask = topTask.createTask("Task/output_Task")

    # == Create shared DLElement ==
    import RootWriter
    root_writer = Sniper.create("SharedElem<RootWriter>/RootWriter")
    root_writer.property("Output").set({"USER_SN":args.user_output,
                                        "USER_PRESN":args.user_output}) #"USER_OUTPUT":args.user_output, 
    topTask.addSvc(root_writer)
    import OECTagSvc
    oec_tagsvc = Sniper.create("SharedElem<OECTagSvc>/OECTagSvc")
    oec_tagsvc.property("OECTagFile").set(os.getenv('ONLINEMONITORROOT')+"/share/tag_SN.json")
    topTask.addSvc(oec_tagsvc)

    # == Configure topTask ==
    import JunoTimer
    topTask.createSvc("JunoTimerSvc")
    import OECProcessor
    oecprocessoralg = topTask.createAlg("OECProcessorAlg")
    oecprocessoralg.property("TimeWindow").set([-0.01, 0.01])

    # == Configure input_Task ==
    filelist=[]
    if args.input:
        filelist.append(args.input)
    if args.inputList:
        for fname in args.inputList:
            with open(fname) as hxf:
                for line in hxf:
                    line=line.strip()
                    filelist.append(line)
    import BufferMemMgr
    bufmgr = inputTask.createSvc("BufferMemMgr")
    bufmgr.property("StopTaskOpt").set(1)
    import RootIOSvc
    readin=inputTask.createSvc("RootInputSvc/InputSvc")
    readin.property("InputFile").set(filelist)

    # == Configure LEC_Task ==
    LECTask.addSvc(root_writer)
    LECTask.addSvc(oec_tagsvc)
    import BufferMemMgr
    lecbufmgr = LECTask.createSvc("BufferMemMgr")
    import EvtStore
    LECTask.createSvc('EvtStoreSvc')
    import JunoTimer
    LECTask.createSvc("JunoTimerSvc")
    import OECProcessor
    LECTask.createSvc("OECCreatorAlg")
    import EvtSteering
    stephandler = LECTask.createAlg("StepHandler")
    stepsequencer = stephandler.createTool("StepSequencer")
    stepsequencer.property("ConfigFile").set(os.getenv('ONLINEMONITORROOT')+"/share/seq_SN.json")
    stepdecision = stephandler.createTool("StepDecision")
    stepdecision.property("ConfigFile").set(os.getenv('ONLINEMONITORROOT')+"/share/sig_SN.json")
    # = Import reconstruction algorithms to be used =
    import readFromRecAlg

    # == Configure HEC_Task ==
    HECTask.addSvc(root_writer)
    HECTask.addSvc(oec_tagsvc)
    import OECConfigSvc
    OECConf = HECTask.createSvc("OECConfigSvc")
    if args.configFile:
        OECConf.property("OECListFile").set(args.configFile)
    else:
        OECConf.property("OECListFile").set(os.getenv('ONLINEMONITORROOT')+"/share/tagCond.json")

    # = The classification algorithm to select IBD =
    import HECAlg
    hecalg = HECTask.createAlg("HECAlg")
    hecalg.property("toolName").set(["SNClassTool"])
    import SNClassTool
    tool_snclass = hecalg.createTool("SNClassTool")
    tool_snclass.property("maxN").set(100)
    tool_snclass.property("dT").set(1500000)

    # = The CCSN Monitor algorithm =
    import OnlineMonitor
    onlinemonitor = HECTask.createAlg("OnlineMonitor")
    onlinemonitor.property("specifyBeginTime").set(args.specifiedStart)
    onlinemonitor.property("beginTime").set(args.beginTime)
    onlinemonitor.property("useToyBkg_sn").set(args.toybkg_sn)
    onlinemonitor.property("useToyBkg_pre").set(args.toybkg_pre)
    onlinemonitor.property("seed").set(args.seed)

    sntool = onlinemonitor.createTool(args.monitorMethod+'/sn')
    presntool = onlinemonitor.createTool(args.monitorMethod+'/presn')
    
    if args.monitorMethod == 'SlidingWindow':
        sntool.property('slideT').set(args.sn_T)
        sntool.property('freshT').set(args.sn_dT)
        sntool.property('Nthr').set(args.sn_Nthr)
        sntool.property('startTime').set(args.sn_startTime)
        presntool.property('slideT').set(args.presn_T)
        presntool.property('freshT').set(args.presn_dT)
        presntool.property('Nthr').set(args.presn_Nthr)
        presntool.property('startTime').set(args.presn_startTime)
    elif args.monitorMethod == 'TimeInterval':
        sntool.property("T").set(args.sn_T)
        sntool.property("Nthr").set(args.sn_Nthr)
        sntool.property("startTime").set(args.sn_startTime)
        presntool.property("T").set(args.presn_T)
        presntool.property("Nthr").set(args.presn_Nthr)
        presntool.property("startTime").set(args.presn_startTime)
    elif args.monitorMethod == 'BayesianBlock':
        sntool.property('ncp_prior').set(args.sn_ncp)
        presntool.property('ncp_prior').set(args.presn_ncp)

    # == Configure output_Task ==
    import BufferMemMgr
    outbufmgr = outputTask.createSvc("BufferMemMgr")
    if args.output:
        import RootIOSvc
        readout = outputTask.createSvc("RootOutputSvc/OutputSvc")
        outputdata = {"/Event/SN": args.output,
                    "/Event/Oec": args.output}
        readout.property("OutputStreams").set(outputdata)

    # == Run the code ==
    topTask.show()
    topTask.run()

