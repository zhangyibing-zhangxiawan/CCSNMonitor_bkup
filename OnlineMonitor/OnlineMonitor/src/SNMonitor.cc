#include "SNMonitor.h"
#include "SniperKernel/SniperLog.h"
#include "MonitorMethod/SlidingWindow.h"
#include "MonitorMethod/BayesianBlock.h"
#include "MonitorMethod/TimeInterval.h"

SNMonitor::SNMonitor(){
    //m_rnd = NULL;
    m_lastBkg = TTimeStamp(-10*24*3600, 0);  
    dir_tbeg = -1;
    dir_tend = 19;
    LogInfo<<"TEST IN SNMonitor!!!!!! m_lastBkg="<<m_lastBkg<<" dir_tbeg="<<dir_tbeg<<" dir_tend="<<dir_tend<<std::endl;
} 

SNMonitor::~SNMonitor(){
    //delete m_rnd;
}

void SNMonitor::cache(const JM::SNEvent *thisevent){
    //Don't cache toy backgrounds
    if (b_toyMuon){
        TTimeStamp thistime = thisevent->getPromptTime();
        genToyMuon(thistime);
        if (muonVeto(thistime)) return;
    }
    m_candCache.push_back(thisevent);
}

void SNMonitor::add(const TTimeStamp &thistime){ //m_SNMonitor->add(tEventSN->getPromptTime());
    if (b_toyMuon){
        genToyMuon(thistime);
    }
    //Add the newly found candidates
    if (b_toyBkg){
        LogInfo<<"TEST IN SNMonitor!!! m_lastBkg="<<m_lastBkg<<" thistime="<<thistime<<std::endl;
        double rbkg = 127./(24*3600.);
        while (m_lastBkg<thistime){  //TTimeStamp m_lastBkg
            if (b_toyMuon && !muonVeto(m_lastBkg)){
                m_candBuffer.push_back(m_lastBkg);
                LogDebug<<"toy bkg time:"<<m_lastBkg<<std::endl;
                std::cout<<"toy bkg time:"<<m_lastBkg<<std::endl;
            }
            else if (!b_toyMuon){
                m_candBuffer.push_back(m_lastBkg);
                LogDebug<<"toy bkg time:"<<m_lastBkg<<std::endl;
                std::cout<<"toy bkg time:"<<m_lastBkg<<std::endl;
            }
            double dt=m_rnd->Exp(1./rbkg);
            int sec=int(dt);
            int nanosec=int((dt-sec)*1e9);
            m_lastBkg.Add(TTimeStamp(sec,nanosec));
        }
    }
    m_candBuffer.push_back(thistime);////For newly added candidates
    
    LogInfo<<"TEST IN SNMonitor!!! m_candBuffer.size()="<<m_candBuffer.size()<<" thistime="<<thistime<<std::endl;
}

MonitorMessage SNMonitor::monitorOnce(MonitorStatus &thestatus){
    if (thestatus==MonitorStatus::noAlert){
        //Find the alert in m_candMonitor
        std::string methodname = dynamic_cast<ToolBase*>(m_methodTool)->tag();
        std::deque<TTimeStamp> alertCand = m_methodTool->findAlert(m_candMonitor);
        bool isfound = findAlertTime(alertCand, methodname);
        if (isfound){
            thestatus = MonitorStatus::snAlert;
            return MonitorMessage::newAlert;
        }
        else return MonitorMessage::noMessage;
    }
    else if (thestatus==MonitorStatus::preAlert){
        //Find the alert in m_candMonitor
        TTimeStamp preAlertTime = m_alertTime;
        std::string methodname = dynamic_cast<ToolBase*>(m_methodTool)->tag();
        std::deque<TTimeStamp> alertCand = m_methodTool->findAlert(m_candMonitor);
        bool isfound = findAlertTime(alertCand, methodname);
        if (isfound){
            if (m_alertTime-preAlertTime<24*3600) thestatus = MonitorStatus::nearbyAlert;
            else thestatus = MonitorStatus::snAlert;
            return MonitorMessage::newAlert;
        }
        else {
            return MonitorMessage::noMessage;
        }
    }
    else if (thestatus==MonitorStatus::snAlert || thestatus==MonitorStatus::nearbyAlert){
        //MonitorStatus::snAlert lasts for 1min
        TTimeStamp curTime = m_candMonitor.back();
        TTimeStamp lastAlertTime = m_alertTime;
        if (curTime-lastAlertTime>dir_tend){
            TTimeStamp slTime = m_candMonitor[m_candMonitor.size()-2];//second to last event
            if (slTime-lastAlertTime<dir_tend){
                calDirection();
                return MonitorMessage::newDirection;
            }
        }
        if (curTime-lastAlertTime>60){
            thestatus = MonitorStatus::noAlert;
            return MonitorMessage::noMessage;
        }
    }
    return MonitorMessage::noMessage;
}

MonitorMessage SNMonitor::monitor(MonitorStatus &thestatus){
    std::vector<MonitorMessage> messages;
    while (m_candBuffer.size()!=0){
        TTimeStamp newcand = m_candBuffer.front();
        m_candMonitor.push_back(newcand); //std::deque<TTimeStamp> m_candMonitor;//For performing alert algorithms
        m_candBuffer.pop_front(); //std::deque<TTimeStamp> m_candBuffer;//For newly added candidates
        //remove too early events
        //if use sliding window method: reserve events within 60s
        //if use bayesian block method: reserve 1000 events
        //if use time interval method:  reserve 100 events
        TTimeStamp thistime = m_candMonitor.back();
        std::string methodname = dynamic_cast<ToolBase*>(m_methodTool)->tag();
        if (!methodname.compare("SlidingWindow")){
            for (double thisevtt : m_candMonitor){
                if (thistime.AsDouble()-thisevtt<60) break;
                m_candMonitor.pop_front();
            }
        }
        else if (!methodname.compare("TimeInterval")){
            int totEvts = m_candMonitor.size();
            while(totEvts>100){
                m_candMonitor.pop_front();
                totEvts--;
            }
        }
        else if (!methodname.compare("BayesianBlock")){
            int totEvts = m_candMonitor.size();
            while(totEvts>1000){
                m_candMonitor.pop_front();
                totEvts--;
            }
        }
        else{
            LogError<<"Unrecongnized moitoring method!"<<std::endl;
        }

        if (m_candMonitor.back()<m_tbeg) continue;

        MonitorMessage themessage = monitorOnce(thestatus);
        if (themessage==MonitorMessage::noMessage) continue;
        else messages.push_back(themessage);
    }// while (m_candBuffer.size()!=0)

    if (messages.size()==0) return MonitorMessage::noMessage;
    else{
        MonitorMessage themessage = messages.back();
        return themessage;
    }
    
}//MonitorMessage SNMonitor::monitor(MonitorStatus &thestatus)


bool SNMonitor::muonVeto(const TTimeStamp &thistime){
    for (std::deque<TTimeStamp>::iterator it=m_muTime.begin();it!=m_muTime.end();++it){
        if ((*it)>thistime) break;
        if (thistime-(*it)<1e-3) return true;
    }
    return false;
}

bool SNMonitor::findAlertTime(const std::deque<TTimeStamp>& alertCand, std::string method){
    //find the alert, in this case only give one alert
    if (!method.compare("SlidingWindow") || !method.compare("TimeInterval")){
        if (alertCand.size()>0){
            m_alertTime = m_candMonitor.back();
            LogInfo<< "Find an alert!!!---[" << alertCand[0] << " ]" <<std::endl;
            return true;
        }
    }
    else if (!method.compare("BayesianBlock")){
        const int evtnumb = m_candMonitor.size();
        const int blocknumb = alertCand.size()+1;
        if (blocknumb>1){
            //get the rate in each block
            std::vector<double> vrate(blocknumb);
            int ith = 0;
            for (int ii=0;ii<blocknumb;ii++){
                //TTimeStamp tend = alertCand[ii];
                int nsum = 0;
                for (;ith<evtnumb;ith++){
                    if (ii<blocknumb-1){
                        if (m_candMonitor[ith]>alertCand[ii]) break;
                    }
                    nsum++;
                }
                double dt = 0;
                if (ii==0) dt = alertCand[ii]-m_candMonitor.front();
                else if (ii==blocknumb-1) dt = m_candMonitor.back()-alertCand.back();
                else dt = alertCand[ii]- alertCand[ii-1];
                vrate[ii] = nsum/dt;
            }

            //check the change point
            for (int ii=blocknumb-2;ii>=0;ii--){
                if (m_candMonitor.back()-alertCand[ii]>20){//time should be within 20s
                    break;
                }
                if (vrate[ii+1]-vrate[ii]<0){//rate should increase
                    continue;
                }
                m_alertTime = m_candMonitor.back();
                LogInfo<< "Find an alert!!!---[" << m_alertTime << " ]" <<std::endl;
                LogInfo<< "The change point is!!!---[" << alertCand[ii] << " ]" <<std::endl;
                return true;
            }
        }
    }
    return false;
}

void SNMonitor::calDirection(){
    m_direction = TVector3(0, 0, 0);
    int totn = 0;
    for (std::deque<const JM::SNEvent*>::reverse_iterator rit=m_candCache.rbegin();rit!=m_candCache.rend();++rit){
        const TTimeStamp curTime = (*rit)->getPromptTime();
        if (curTime-m_alertTime>dir_tend) continue;
        if (curTime-m_alertTime>dir_tbeg){
            float px = (*rit)->getPromptX();
            float py = (*rit)->getPromptY();
            float pz = (*rit)->getPromptZ();
            TVector3 vp(px, py, pz);
            float dx = (*rit)->getDelayedX();
            float dy = (*rit)->getDelayedY();
            float dz = (*rit)->getDelayedZ();
            TVector3 vd(dx, dy, dz);
            m_direction+=(vd-vp).Unit();
            totn+=1;
        }
        else break;
    }
}
