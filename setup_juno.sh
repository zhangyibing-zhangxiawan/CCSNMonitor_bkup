#!/bin/bash

function junotop(){
echo /cvmfs/juno.ihep.ac.cn/centos7_amd64_gcc1120/Pre-Release/J23.1.0-rc1
}

function worktop(){
echo /afs/ihep.ac.cn/users/y/ybzhang/junofs/J22.2.0-rc2
}

export JUNOTOP=$(junotop)
export WORKTOP=$(worktop)
export JUNO_OFFLINE_OFF=1 #0
export CMTCONFIG=amd64_linux26

pushd $JUNOTOP >& /dev/null
source setup.sh
popd >& /dev/null

#pushd $JUNOTOP
pushd $WORKTOP
if [ -f "junosw/InstallArea/setup.sh" ]; then
    echo 'Setup Local Offline Software (CMake version)'
    pushd junosw/InstallArea >& /dev/null
    source setup.sh
    popd >& /dev/null
fi
popd
