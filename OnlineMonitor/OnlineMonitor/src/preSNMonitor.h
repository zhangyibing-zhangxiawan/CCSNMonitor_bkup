#ifndef PRESNMONITOR_H
#define PRESNMONITOR_H
#include "IMonitor.h"

class preSNMonitor: public IMonitor{
    public:
        preSNMonitor();
        ~preSNMonitor();

        virtual void cache(const JM::SNEvent*);
        virtual void add(const TTimeStamp&);
        virtual MonitorMessage monitor(MonitorStatus&);

    private:
        //----------------For generating toy background-----------
        //////////////////////////////////////////////////////////
        //Not generating muon events
        //select 92% of the events randomly instead
        //////////////////////////////////////////////////////////
        //TRandom3 *m_rnd;
        TTimeStamp m_lastBkg;
        bool muonVeto(const TTimeStamp&);

        //---------------For giving the alert-----------------
        bool findAlertTime(const std::deque<TTimeStamp>&, std::string);
        MonitorMessage monitorOnce(MonitorStatus&);
};
#endif
