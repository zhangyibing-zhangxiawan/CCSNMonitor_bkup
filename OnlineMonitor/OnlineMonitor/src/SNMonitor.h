#ifndef SNMONITOR_H
#define SNMONITOR_H
#include "IMonitor.h"

class SNMonitor: public IMonitor{
    public:
        SNMonitor();
        ~SNMonitor();

        virtual void cache(const JM::SNEvent*);
        virtual void add(const TTimeStamp&);
        virtual MonitorMessage monitor(MonitorStatus&);

    private:
        //----------------For generating toy background-----------
        //////////////////////////////////////////////////////////
        //Generating the muon events according to exp distribution
        //Veto the events within 1ms of a muon event
        //////////////////////////////////////////////////////////
        //TRandom3 *m_rnd;
        TTimeStamp m_lastBkg;
        bool muonVeto(const TTimeStamp&);

        //---------------For giving the alert-----------------
        MonitorMessage monitorOnce(MonitorStatus&);
        bool findAlertTime(const std::deque<TTimeStamp>&, std::string);

        //---------------For fast characteristization--------------
        double dir_tbeg;//relative to the alert time
        double dir_tend;
        void calDirection();
};
#endif
