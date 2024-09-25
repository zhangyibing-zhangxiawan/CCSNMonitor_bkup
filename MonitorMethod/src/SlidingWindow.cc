#include "MonitorMethod/SlidingWindow.h"
#include "SniperKernel/ToolFactory.h"

DECLARE_TOOL(SlidingWindow);

SlidingWindow::SlidingWindow(const std::string &name): ToolBase(name){
    declProp("slideT", d_slideT=4);
    declProp("freshT", d_freshT=1e-3);
    declProp("Nthr", i_Nthr=3);
    declProp("startTime", d_tbeg=0);
}

SlidingWindow::~SlidingWindow(){
}

bool SlidingWindow::init(){
    int sec = -30;
    int nanosec =0;
    //curTime
    sec = int(d_tbeg);
    nanosec = int((d_tbeg-sec)*1e9);
    m_par.curTime = TTimeStamp(sec, nanosec);
    //slideT
    sec = int(d_slideT);
    nanosec = int((d_slideT-sec)*1e9);
    m_par.slideT = TTimeStamp(sec, nanosec);
    //freshT
    sec = int(d_freshT);
    nanosec = int((d_freshT-sec)*1e9);
    m_par.freshT= TTimeStamp(sec, nanosec);
    //Nthr
    m_par.Nthr = i_Nthr;
    m_par.print();
    return true;
}

bool SlidingWindow::fina(){
    return true;
}

std::deque<TTimeStamp> SlidingWindow::findAlert(const std::deque<TTimeStamp>& vEvtTime){
    std::deque<TTimeStamp> vAlertTime;
    vAlertTime.clear();
    if (vEvtTime.size()==0) return vAlertTime;

    //By default, assuming the order in vEvtTime is aligned by time
    const TTimeStamp &endTime=vEvtTime.back();
    double t2end=endTime-m_par.curTime;
    if (t2end<0){//curTime has already slide after the end
        //do not slide and give the trigger
        int nevts = 0;
        for (std::deque<TTimeStamp>::const_reverse_iterator rit=vEvtTime.rbegin();rit!=vEvtTime.rend();++rit){
            if (m_par.curTime-*rit>m_par.slideT.AsDouble()) break;
            nevts++;
        }
        if (nevts>m_par.Nthr){
            vAlertTime.push_back(m_par.curTime);
            //LogInfo<< "Find an alert!!!---[" << m_par.curTime << " ]" <<std::endl;
        }
    }
    else{
        //slide and give the trigger
        while (t2end>0){
            m_par.curTime.Add(m_par.freshT);
            int nevts = 0;
            for (std::deque<TTimeStamp>::const_reverse_iterator rit=vEvtTime.rbegin();rit!=vEvtTime.rend();++rit){
                if (*rit>m_par.curTime) continue;
                else if (m_par.curTime-*rit<m_par.slideT.AsDouble()) nevts++;
                else break;
            }
            if (nevts>m_par.Nthr){
                vAlertTime.push_back(m_par.curTime);
                //LogInfo<< "Find an alert!!!---[" << m_par.curTime << " ]" <<std::endl;
                //return vAlertTime;
            }
            t2end=endTime-m_par.curTime;
        }
    }
    return vAlertTime;
}

void SlidingWindow::setCurTime(const TTimeStamp& tmpt){
    m_par.curTime = tmpt;
}

void SlidingWindow::setPar(PAR &thepar){
    m_par.curTime = thepar.curTime;
    m_par.slideT = thepar.slideT;
    m_par.freshT = thepar.freshT;
    m_par.Nthr = thepar.Nthr;
    m_par.print();
}
