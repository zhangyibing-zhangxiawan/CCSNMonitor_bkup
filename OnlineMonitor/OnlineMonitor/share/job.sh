#!/bin/bash

# = This is an example to run the Online Monitor =
# = Parameters used in the command =
noTrail=10 #$1

function genFileList {
    # = Input and output =
    simTopDir=/eos/juno/user/ybzhang
    outFileDir=${ONLINEMONITORROOT}/myJob/fileLists
    if [ ! -d ${outFileDir} ];then
        mkdir -p ${outFileDir}
    fi
    outfile=${ONLINEMONITORROOT}/myJob/fileLists/fileList_${noTrail}.txt
    echo ${outfile}

    # = Generate the file list =
    if [ -f ${outfile} ];then
        rm -f ${outfile}
    fi
    for nthFile in $(seq 0 40)
    do
        recfile=${simTopDir}/rec/10/rec_${nthFile}.root
        #if [ -f ${recfile} ];then
        if eos ls ${recfile} > /dev/null 2>&1;then
            cat >> ${outfile} << EOF
${EOS_MGM_URL}/${recfile}
EOF
        else
            break
        fi
    done
}

function monitorJob {
    # = Source environment =
    ccsnMonitorRoot=/junofs/users/ybzhang/CCSNMonitor
    source ${ccsnMonitorRoot}/setup_juno.sh
    source ${ccsnMonitorRoot}/InstallArea/setup.sh

    # = Parameters =
    monitorMethod=TimeInterval
    useToyBkg=1 #1:TRUE 0:FALSE

    # = Input and output =
    infile=${ONLINEMONITORROOT}/myJob/fileLists/fileList_${noTrail}.txt
    outDir=${ONLINEMONITORROOT}/myJob/result
    if [ ! -d ${outDir} ];then
        mkdir -p ${outDir}
    fi
    edmOutfile=${outDir}/monitor_${noTrail}.root
    userOutfile=${outDir}/user-monitor_${noTrail}.root
    logOutfile=${outDir}/log-monitor_${noTrail}.txt

    # = The job options =
    jobOpt="--evtmax -1 --inputList ${infile} --output ${edmOutfile} --user-output ${userOutfile} --monitorMethod ${monitorMethod}" # --configFile ${configFile}
    if [  ];then
        jobOpt="${jobOpt} --enableSpecifiedStart --beginTime 0"
    else
        jobOpt="${jobOpt} --disableSpecifiedStart"
    fi

    # - Whether to use toy background -
    if [ ${useToyBkg} -eq 1 ];then
        echo Use toy background
        jobOpt="${jobOpt} --enableSNtoybkg --enablePretoybkg"
    elif [ ${useToyBkg} -eq 0 ];then
        echo Do not use toy background
        jobOpt="${jobOpt} --disableSNtoybkg --disablePretoybkg"
    fi

    # - Set Options according to the alert method -
    # - Here, use SN monitor as example -
    if [ ${monitorMethod} = SlidingWindow ];then
        echo SlidingWindow method is used
        jobOpt="${jobOpt} --sn-T 10 --sn-dT 0.1 --sn-Nthr 3 --sn-startTime -5"
    elif [ ${monitorMethod} = TimeInterval ];then
        echo TimeInterval method is used
        jobOpt="${jobOpt} --sn-T 10 --sn-Nthr 3 --sn-startTime -5"
    elif [ ${monitorMethod} = BayesianBlock ];then
        echo BayesianBlock method is used
        jobOpt="${jobOpt} --sn-ncp 7"
    fi


    echo ${logOutfile}
    # = Run the job =
    (time python /junofs/users/ybzhang/CCSNMonitor/OnlineMonitor/OnlineMonitor/share/run.py ${jobOpt}) >& ${logOutfile}
}

#genFileList
monitorJob
