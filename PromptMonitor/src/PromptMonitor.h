#ifndef PROMPTMONITOR_H
#define PROMPTMONITOR_H

#include <vector>
#include "TRandom3.h"
#include "TTree.h"
#include "TTimeStamp.h"

#include "SniperKernel/AlgBase.h"
#include "EvtNavigator/NavBuffer.h"

#include "MonitorMethod/IMonitorMethod.h"

class PromptMonitor: public AlgBase{
    public:
        PromptMonitor(const std::string &name);
        ~PromptMonitor();

        bool initialize();
        bool execute();
        bool finalize();

    private:
        JM::NavBuffer *m_buf;
        TRandom3* m_prnd;
        void generateRndVeto(double, double);
        void generateRndBkg(double, double);
        //int getNFiredPMTbyTruth(double);
        int getNFiredPMT();
        std::deque<double> m_muTime;
        std::deque<double> m_bkgTime;
        std::deque<TTimeStamp> m_evtTime;

        //=============monitor method============
        std::string s_method;
        IMonitorMethod *m_method[2];//0: sn-like,    1: muon-like
        //=============parameters==============
        double d_vetoRate;
        double d_vetoTime;
        double d_bkgRate;
        bool b_toybkg;
        bool b_toymuon;
        //----------for event type-----------
        int i_NpmtLcut;
        int i_NpmtHcut;
        double d_T;//count the number of pmts in d_T

        //===============output=================
        void initOutput();
        //void getEventUser();//for user output of event level
        //------------trigger info---------------
        TTree* ttrig;
        bool b_isTriggered;
        double d_snTriggerTime;
        //--------------evt info---------------
        TTree *tevt;
        int i_totFiredPMTs;
        int i_evtType;//0: sn-like    1: muon-like    2: other
        double d_time;
        double d_Qedep;
        double d_QedepX;
        double d_QedepY;
        double d_QedepZ;
};
#endif
