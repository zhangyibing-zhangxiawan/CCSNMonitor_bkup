#include "MonitorMethod/TimeInterval.h"
#include "SniperKernel/ToolFactory.h"

DECLARE_TOOL(TimeInterval);

TimeInterval::TimeInterval(const std::string& name): ToolBase(name){
    declProp("T", d_T=10);
    declProp("Nthr", i_Nthr=2);
    declProp("startTime", d_tbeg=0);
}

TimeInterval::~TimeInterval(){
}

bool TimeInterval::init(){
    int sec = -30;
    int nanosec =0;
    //curTime
    sec = int(d_tbeg);
    nanosec = int((d_tbeg-sec)*1e9);
    m_par.curTime = TTimeStamp(sec, nanosec);
    //T
    sec = int(d_T);
    nanosec = int((d_T-sec)*1e9);
    m_par.T = TTimeStamp(sec, nanosec);
    //Nthr
    m_par.Nthr = i_Nthr;

    m_par.print();
    return true;
}

bool TimeInterval::fina(){
    return true;
}

std::deque<TTimeStamp> TimeInterval::findAlert(const std::deque<TTimeStamp>& vEvtTime){ //vEvtTime size 100
    LogInfo << "m_par.T = "<<m_par.T<<" m_par.curTime = "<< m_par.curTime<<std::endl;

    std::deque<TTimeStamp> vAlertTime;
    vAlertTime.clear();
    if (vEvtTime.size()==0) return vAlertTime;

    //By default, assuming the order in vEvtTime is aligned by time
    //First, check whether current time is too eraly or late
    if (m_par.curTime<vEvtTime.front()){
        LogWarn<<"Too early current time!"<<std::endl;
        m_par.curTime = vEvtTime.front();
    }
    
    std::deque<TTimeStamp>::const_reverse_iterator rit_cur = vEvtTime.rbegin();

    if (m_par.curTime>=*rit_cur){
        LogWarn<<"Too late current time!Wait for more events"<<std::endl;
        return vAlertTime;
    }
    //if (vEvtTime.size()<m_par.Nthr+1){
    //    LogWarn<<"Not enough events!"<<std::endl;
    //    return vAlertTime;
    //}
    //Then, find the iterator of the event right after curTime
    while (rit_cur!=vEvtTime.rend()){
        auto rit_pevt = rit_cur + 1;
        if (*rit_pevt<=m_par.curTime && *rit_cur>m_par.curTime) break;
        rit_cur++;
    }

    //Finally, find the alert and update the current time

    while (rit_cur>=vEvtTime.rbegin()){
        if (vEvtTime.rend()-rit_cur<m_par.Nthr+1){ //Not enough previous events //m_par.Nthr:3
            LogWarn<<"Not enough previous events!Please buffer more!"<<std::endl;
            m_par.curTime = *rit_cur;
            rit_cur--;
            continue;
        }
        m_par.curTime = *rit_cur;
        std::deque<TTimeStamp>::const_reverse_iterator rit_beg = rit_cur + m_par.Nthr;
        double dt = *rit_cur-*rit_beg;

        if (dt<m_par.T){ //find the alert //4 for presn, 10 for sn.
            vAlertTime.push_back(m_par.curTime);
        }
        rit_cur--;
    } //while (rit_cur>=vEvtTime.rbegin())

    
    return vAlertTime;
}



void TimeInterval::setCurTime(const TTimeStamp& tmpt){
    LogInfo<<"tmpt in setCurTime() = "<<tmpt<<std::endl;
    m_par.curTime = tmpt;
};

void TimeInterval::setPar(PAR& thepar){
  LogInfo<<"In setPar():"<<" thepar.curTime="<<thepar.curTime<<" thepar.T="<<thepar.T<<" thepar.Nthr="<<thepar.Nthr<<std::endl;
    m_par.curTime = thepar.curTime;
    m_par.T = thepar.T;
    m_par.Nthr = thepar.Nthr;
    m_par.print();
}
