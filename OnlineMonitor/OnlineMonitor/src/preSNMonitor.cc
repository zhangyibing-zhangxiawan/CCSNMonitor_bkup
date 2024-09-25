#include "preSNMonitor.h"
#include "SniperKernel/SniperLog.h"
#include "MonitorMethod/SlidingWindow.h"
#include "MonitorMethod/BayesianBlock.h"
#include "MonitorMethod/TimeInterval.h"

preSNMonitor::preSNMonitor(){
    //m_rnd=new TRandom3(0);
    m_lastBkg = TTimeStamp(-(30+50)*24*3600, 0);
}

preSNMonitor::~preSNMonitor(){
    //delete m_rnd;
}

void preSNMonitor::cache(const JM::SNEvent *thisevent){
    if (b_toyMuon){
        TTimeStamp thistime = thisevent->getPromptTime();
        if (muonVeto(thistime)) return;
    }
    m_candCache.push_back(thisevent);
}

void preSNMonitor::add(const TTimeStamp &thistime){
    if (b_toyBkg){
        //double rbkg = 27.3/(24*3600.)/0.92;//27.3 is the rate after muon veto
        double rbkg = 21./(24*3600.)/0.92;//For 26.6GW thermal power
        while (m_lastBkg<thistime){
            if (b_toyMuon && !muonVeto(m_lastBkg)){
                m_candBuffer.push_back(m_lastBkg);
                std::cout<<"preSNMonitor.add: toy bkg time:"<<m_lastBkg<<std::endl;
                LogDebug<<"toy bkg time:"<<m_lastBkg<<std::endl;
            }
            else if (!b_toyMuon){
                m_candBuffer.push_back(m_lastBkg);
                std::cout<<"preSNMonitor.add: toy bkg time:"<<m_lastBkg<<std::endl;
                LogDebug<<"toy bkg time:"<<m_lastBkg<<std::endl;
            }
            double dt=m_rnd->Exp(1./rbkg);
            int sec=int(dt);
            int nanosec=int((dt-sec)*1e9);
            m_lastBkg.Add(TTimeStamp(sec,nanosec));
        }
    }
    if (b_toyMuon && !muonVeto(thistime)) m_candBuffer.push_back(thistime);
    else if (!b_toyMuon) m_candBuffer.push_back(thistime);
}

MonitorMessage preSNMonitor::monitorOnce(MonitorStatus &thestatus){
    if (thestatus==MonitorStatus::noAlert){
        //Find the alert in m_candMonitor
        std::string methodname = dynamic_cast<ToolBase*>(m_methodTool)->tag();
        std::deque<TTimeStamp> alertCand = m_methodTool->findAlert(m_candMonitor);
        bool isfound = findAlertTime(alertCand, methodname);
        if (isfound){
            thestatus = MonitorStatus::preAlert;
            return MonitorMessage::newAlert;
        }
        else return MonitorMessage::noMessage;
    }
    else if (thestatus==MonitorStatus::snAlert || thestatus==MonitorStatus::nearbyAlert){
        return MonitorMessage::noMessage;
    }
    else if (thestatus==MonitorStatus::preAlert){
        //MonitorStatus::preAlert lasts for 30 days, this value now is for test
        TTimeStamp curTime = m_candMonitor.back();
        if (curTime-m_alertTime>30*24*3600){
            thestatus = MonitorStatus::noAlert;
            return MonitorMessage::noMessage;
        }
    }
    return MonitorMessage::noMessage;
}

MonitorMessage preSNMonitor::monitor(MonitorStatus &thestatus){
    std::vector<MonitorMessage> messages;
    while (m_candBuffer.size()!=0){
        TTimeStamp newcand = m_candBuffer.front();
        m_candMonitor.push_back(newcand);
        m_candBuffer.pop_front();
        //for (TTimeStamp newcand : m_candBuffer){//Only monitor when this event is signal
        //    m_candMonitor.push_back(newcand);
        //}
        //m_candBuffer.clear();

        //remove too early events
        //if use sliding window method: reserve events within 1day
        //if use bayesian block method: reserve 1000 events
        //if use time interval method:  reserve 100 events
        TTimeStamp thistime = m_candMonitor.back();
        std::string methodname = dynamic_cast<ToolBase*>(m_methodTool)->tag();
        if (!methodname.compare("SlidingWindow")){
            for (double thisevtt : m_candMonitor){
                if (thistime.AsDouble()-thisevtt<24*3600) break;
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

        if (m_candMonitor.back()<m_tbeg) continue;

        MonitorMessage themessage = monitorOnce(thestatus);
        if (themessage==MonitorMessage::noMessage) continue;
        else messages.push_back(themessage);
    }

    if (messages.size()==0) return MonitorMessage::noMessage;
    else{
        MonitorMessage themessage = messages.back();
        return themessage;
    }
}

bool preSNMonitor::muonVeto(const TTimeStamp &thisTime){
    bool vetoed = (m_rnd->Uniform(0, 1)>0.92);
    return vetoed;
}

bool preSNMonitor::findAlertTime(const std::deque<TTimeStamp>& alertCand, std::string method){
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
                //if (m_candMonitor.back()-alertCand[ii]>20){//time should be within 20s
                //    break;
                //}
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
