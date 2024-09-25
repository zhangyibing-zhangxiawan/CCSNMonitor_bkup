#ifndef ONLINEMONITOR_H
#define ONLINEMONITOR_H
#include "IMonitor.h"
#include "Event/OecHeader.h"
#include "SniperKernel/AlgBase.h"
#include "EvtNavigator/NavBuffer.h"
#include "TTree.h"

class OnlineMonitor: public AlgBase{
    public:
        OnlineMonitor(const std::string&);
        ~OnlineMonitor();

        bool initialize();
        bool execute();
        bool finalize();

    private:
        ////----------------For generating toy background-----------
        ///////////////////////////////////////////////////////
        ////For SN: generating toy muons and perform muon veto
        ////For pre-SN: do not generate muons, just select 0.92 of them
        bool b_sntoybkg;
        bool b_pretoybkg;
        int i_seed;
        TRandom3 *m_rnd;
        ///////////////////////////////////////////////////////
        //TRandom3 *m_rnd;//For toy MC and toy veto
        //std::deque<TTimeStamp> m_muTime;//for sn muon veto
        //std::deque<TTimeStamp> m_bkgTime;//for background IBD

        JM::NavBuffer *m_buf;
        bool b_specifyBeginTime_sn;
        bool b_specifyBeginTime_presn;
        double d_tbeg;

        //The monitors
        /////////////////////////////////////////////////////
        //Classify events into different types:
        //sn, pre-sn, both
        //SNMonitor: sn, both
        //preSNMonitor: pre-sn, both
        /////////////////////////////////////////////////////
        MonitorStatus m_status;
        IMonitor *m_SNMonitor;
        IMonitor *m_preSNMonitor;
        std::string getEventType(JM::OecEvt*);

        //For the result output
        TTree *m_treeSN;
        TTree *m_treepreSN;
        double d_alertTime;
        double d_dirx;
        double d_diry;
        double d_dirz;
};
#endif
