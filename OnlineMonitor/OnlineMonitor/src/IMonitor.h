#ifndef IMONITOR_H
#define IMONITOR_H
#include "Event/SNEvent.h"
#include "monitorDef.h"
#include "TRandom3.h"
#include "TTimeStamp.h"
#include "TVector3.h"

#include <deque>

class IMonitorMethod;
class IMonitor{
    public:
        IMonitor();
        virtual ~IMonitor();

        virtual void cache(const JM::SNEvent*) = 0;
        virtual void add(const TTimeStamp&) = 0;//add a new event to be monitored
        virtual MonitorMessage monitor(MonitorStatus&) = 0;

        //set functions
        void setMethod(IMonitorMethod *thistool){m_methodTool=thistool;}
        void setRndGen(TRandom3* rnd){m_rnd=rnd;}
        void setBeginTime(const TTimeStamp& tbeg){m_tbeg=tbeg;}

        //get functions
        TTimeStamp getAlertTime(){return m_alertTime;}
        TVector3 getDirection(){return m_direction;}

        //----------------For toy background and muon-----------
        void useToyBkg(){b_toyBkg=true;}
        void disableToyBkg(){b_toyBkg=false;}
        void useToyMuon(){b_toyMuon=true;}
        void disableToyMuon(){b_toyMuon=false;}

    protected:
        //----------------For generating toy background-----------
        ///////////////////////////////////////////////////////
        //All members share the same muons
        //Toy background is owned by child class
        ///////////////////////////////////////////////////////
        bool b_toyBkg;
        bool b_toyMuon;
        TRandom3* m_rnd;//For toy MC and toy veto
        static std::deque<TTimeStamp> m_muTime;
        void genToyMuon(const TTimeStamp&);

        TTimeStamp m_tbeg;//starts monitor when m_candMonitor.back()>m_tbeg
        std::deque<const JM::SNEvent*> m_candCache;//For fast characterization
        std::deque<TTimeStamp> m_candBuffer;//For newly added candidates
        //There is a possibility that alert algorithm be performed once after buffer several events.
        std::deque<TTimeStamp> m_candMonitor;//For performing alert algorithms

        IMonitorMethod *m_methodTool;//The method used for monitoring

        //-----------------Monitor quantities---------------------
        TTimeStamp m_alertTime;
        TVector3 m_direction;

    private:
};
#endif
