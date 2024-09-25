#include "IMonitor.h"
#include "SniperKernel/SniperLog.h"
#include <iostream>

std::deque<TTimeStamp> IMonitor::m_muTime;
IMonitor::IMonitor(){
    m_rnd = NULL;//new TRandom3(0);
    m_tbeg = TTimeStamp(0, 0);
    m_alertTime = TTimeStamp(-365*24*3600, 0);
    m_direction = TVector3(0, 0, 0);
}

IMonitor::~IMonitor(){
    //delete m_rnd;
}

void IMonitor::genToyMuon(const TTimeStamp &tend){
   LogInfo<<"TEST IN IIMonitor!!!!!! This is the beginning of the genToyMuon function!"<<std::endl;
   double rmuon = 3.6;
   //set the first muon

    if (m_muTime.size()==0){
        TTimeStamp firstmuon = tend;
        firstmuon.Add(TTimeStamp(-300, 0));
        m_muTime.push_back(firstmuon);
	LogInfo<<"TEST IN IIMonitor!!!!!! firstmuon="<<firstmuon<<std::endl;
    }

    
    //add muons until time is 2s latter than tend
    TTimeStamp latestMuon=m_muTime.back();
    LogInfo<<"TEST IN IIMonitor!!!!!! latestMuon="<<latestMuon<<" m_muTime.size()="<<m_muTime.size()<<std::endl;
    
    double t2end=latestMuon-tend;
    LogInfo<<"TEST IN IIMonitor!!!!!! t2end="<<t2end<<" latestMuon="<<latestMuon<<" tend="<<tend<<std::endl;
    
    while (t2end<2){
        double dt=m_rnd->Exp(1./rmuon);
        t2end+=dt;
        int sec=int(dt);
        int nanosec=int((dt-sec)*1e9);
        latestMuon.Add(TTimeStamp(sec, nanosec));
        m_muTime.push_back(latestMuon);
        //LogInfo<<"TEST IN IIMonitor!!!!!! gen an muon:"<<latestMuon<<std::endl;
    }

    LogInfo<<"TEST IN IIMonitor!!!!!! m_muTime.size()="<<m_muTime.size()<<" m_muTime.front()="<<m_muTime.front()<<" latestMuon="<<latestMuon<<std::endl;
    
    //remove muons until time is 2s earlier than tend
    TTimeStamp earlistMuon=m_muTime.front();
    double t2begin=tend-earlistMuon;
    while (t2begin>2){
        m_muTime.pop_front();
        if (m_muTime.size()<=1) break;
        earlistMuon=m_muTime.front();
        t2begin=tend-earlistMuon;
    }

     LogInfo<<"TEST IN IIMonitor!!!!!! m_muTime.size()="<<m_muTime.size()<<" earlistMuon="<<earlistMuon<<" latestMuon"<<latestMuon<<std::endl;
     LogInfo<<"TEST IN IIMonitor!!!!!! This is the end of the genToyMuon function!"<<std::endl;
}
