#include "PromptMonitor.h"
#include "MonitorMethod/SlidingWindow.h"

#include "SniperKernel/AlgFactory.h"
#include "EvtNavigator/EvtNavHelper.h"
#include "RootWriter/RootWriter.h"
//#include "Event/ElecHeader.h"
//#include "Event/CalibHeader.h"
//#include "Event/ElecTruthHeader.h"
#include "Event/CdLpmtCalibHeader.h"
#include "Event/CdLpmtElecTruthHeader.h"
#include "TSystem.h"
DECLARE_ALGORITHM(PromptMonitor);

PromptMonitor::PromptMonitor(const std::string &name):AlgBase(name){
    declProp("useToyBKG", b_toybkg=true);
    declProp("useToyMuon", b_toymuon=true);
    declProp("npmtcut_low", i_NpmtLcut=11500);
    declProp("npmtcut_high", i_NpmtHcut=29000);
    //for the monitor method
    declProp("Method", s_method="SlidingWindow");

    m_prnd = new TRandom3(0);

    d_vetoRate = 3.6;//Hz
    d_vetoTime = 1.5e-3;//s 
    d_bkgRate = 0.0023;//Hz
    d_T = 1008;//ns

    b_isTriggered = false;
    d_snTriggerTime = 0;
}

PromptMonitor::~PromptMonitor(){
}

bool PromptMonitor::initialize(){
    //Check whether the method used has been defined
    if (s_method.compare("SlidingWindow") && s_method.compare("TimeInterval") && s_method.compare("BayesianBlock")){
        LogError<<"Unknow alert method"<<std::endl;
        return false;
    }
    //initialize the monitor method to be used
    m_method[0] = tool<IMonitorMethod>("snlike");
    //m_method[0] = tool<IMonitorMethod>(s_method+"/snlike");
    if (!m_method[0]){
        LogError<<"The monitor tool for sn-like events is not found!"<<std::endl;
        return false;
    }
    if (!m_method[0]->init()){
        LogError<<"Error when initializing the monitor tool:"<<s_method<<std::endl;
        return false;
    }
    m_method[1] = NULL;//tool<IMonitorMethod>(s_method+"/muonlike");
    //if (!s_method.compare("SlidingWindow")){
    //    LogInfo<<"Using sliding window method to monitor CCSN!"<<std::endl;
    //    SlidingWindow *thismethod = dynamic_cast<SlidingWindow*>(m_method[0]);
    //    //for sn-like events
    //    SlidingWindow::PAR snlikepar;
    //    snlikepar.curTime = TTimeStamp(-30, 0);
    //    snlikepar.slideT = TTimeStamp(4, 0);
    //    snlikepar.freshT = TTimeStamp(0, 1000000);
    //    snlikepar.Nthr = i_nthr;
    //    m_method[0] = new SlidingWindow(snlikepar);

    //    //for muon-like events
    //    //this kind of events is not monitored any more, just place here in case
    //    SlidingWindow::PAR muonlikepar;
    //    muonlikepar.curTime = TTimeStamp(-30, 0);
    //    muonlikepar.slideT = TTimeStamp(0, 100000000);
    //    muonlikepar.freshT = TTimeStamp(0, 1000000);
    //    muonlikepar.Nthr = 8;
    //    m_method[1] = new SlidingWindow(muonlikepar);
    //}
    //else{
    //    LogError<<"Unrecongnized monitor method!"<<std::endl;
    //    return false;
    //}

    //get the buffer
    SniperDataPtr<JM::NavBuffer> navBuf(getParent(), "/Event");
    if ( navBuf.invalid() ) {
        LogError << "cannot get the NavBuffer @ /Event" << std::endl;
        return false;
    }
    m_buf = dynamic_cast<JM::NavBuffer*>(navBuf.data());

    //user output
    SniperPtr<RootWriter> rwsvc(getParent(), "RootWriter");
    if (rwsvc.invalid()){
        LogError<<"can not get the root writer service!"<<std::endl;
        return false;
    }
    ttrig=rwsvc->bookTree(*getParent(), "ttrig", "trigger information");
    ttrig->Branch("snTriggerTime", &d_snTriggerTime, "snTriggerTime/D");
    tevt=rwsvc->bookTree(*getParent(), "tevt", "event information");
    tevt->Branch("evtType", &i_evtType, "evtType/I");
    tevt->Branch("time", &d_time, "time/D");
    tevt->Branch("totFiredPMTs", &i_totFiredPMTs, "totFiredPMTs/I");
    tevt->Branch("Qedep",     &d_Qedep,            "Qedep/D");
    tevt->Branch("QedepX",    &d_QedepX,           "QedepX/D");
    tevt->Branch("QedepY",    &d_QedepY,           "QedepY/D");
    tevt->Branch("QedepZ",    &d_QedepZ,           "QedepZ/D");
    rwsvc->attach("SN_TRIGGER", ttrig);
    rwsvc->attach("SN_TRIGGER", tevt);

    //toy bkg and muons
    if (b_toymuon){
        generateRndVeto(-60, 60);
    }
    if (b_toybkg){
        generateRndBkg(-200*3600, 12*3600);
        //double t0 = m_bkgTime[0];//first evtTime is m_bkgTime[0]
        //int sec = int(t0);
        //int nanosec = int((t0-sec)*1e9+1);
        //m_evtTime.push_back(TTimeStamp(sec, nanosec));
    }
    //else{
    //    m_evtTime.push_back(TTimeStamp(-10000000, 0));
    //}
    return true;
}

bool PromptMonitor::finalize(){
    if (!m_method[0]->fina()){
        LogError<<"Error when finalizing the monitor tool:"<<s_method<<std::endl;
        return false;
    }
    return true;
}

bool PromptMonitor::execute(){
    initOutput();
    //monitor the memory usage
    ProcInfo_t info;
    gSystem->GetProcInfo(&info);
    float f_memory = info.fMemResident/1024;
    LogInfo<<"memory used is:"<<f_memory<<std::endl;
    //get the current calib event
    JM::EvtNavigator *tnav=m_buf->curEvt();
    JM::CdLpmtCalibHeader* header_calib = JM::getHeaderObject<JM::CdLpmtCalibHeader>(tnav);
    if (!header_calib->hasEvent()){
        LogInfo<<"CdLpmtCalibEvt doesn't exist, skip it!"<<std::endl;
        return true;
    }

    //classify the current event
    TTimeStamp &thist =tnav->TimeStamp();
    d_time = thist.AsDouble();
    LogDebug<<"global trigger time is:"<<thist<<std::endl;
    i_totFiredPMTs=getNFiredPMT();//getNFiredPMTbyTruth(gtTime);
    LogDebug<<"total fired pmts:"<<i_totFiredPMTs<<std::endl;
    if (i_totFiredPMTs<=0){
        LogWarn<<"An event with less than one fired pmt!"<<std::endl;
        return true;
    }
    if (i_totFiredPMTs>i_NpmtHcut){//muon like
        i_evtType = 1;
    }
    else if (i_totFiredPMTs>i_NpmtLcut){//sn like
        i_evtType = 0;
    }
    else{
        i_evtType = 2;
    }

    //getEventUser();
    tevt->Fill();

    if (b_isTriggered){
        LogInfo<<"Alert has been already found!"<<std::endl;
        return true;
    }

    //pop too early muon events
    for (double thismut : m_muTime){
        if (thismut-thist.AsDouble()>-5) break;
        m_muTime.pop_front();
    }
    //copy bkgTime into evtTime
    for (double thissnt : m_bkgTime){
        if (thissnt-thist.AsDouble()>0) break;
        m_evtTime.push_back(thissnt);
        m_bkgTime.pop_front();
    }
    //copy thist into evtTime
    if (i_evtType == 0){
        m_evtTime.push_back(thist);
    }
    //pop too early events
    if (!s_method.compare("SlidingWindow") || !s_method.compare("TimeInterval")){
        for (double thisevtt : m_evtTime){
            if (thist.AsDouble()-thisevtt<60) break;
            m_evtTime.pop_front();
        }
    }
    else if (!s_method.compare("BayesianBlock")){
        int totEvts = m_evtTime.size();
        while(totEvts>1000){
            m_evtTime.pop_front();
            totEvts--;
        }
    }

    //find the alert, in this case only give one alert
    std::cout<<"HX:"<<m_evtTime.size()<<std::endl;
    std::deque<TTimeStamp> alertTime = m_method[0]->findAlert(m_evtTime);
    if (!s_method.compare("SlidingWindow") || !s_method.compare("TimeInterval")){
        if (alertTime.size()>0){
            b_isTriggered = true;
            d_snTriggerTime = alertTime[0].AsDouble();
            ttrig->Fill();
            LogInfo<< "Find an alert!!!---[" << alertTime[0] << " ]" <<std::endl;
        }
    }
    else if (!s_method.compare("BayesianBlock")){
        std::cout<<"bayesian block size:"<<alertTime.size()<<std::endl;
        const int evtnumb = m_evtTime.size();
        const int blocknumb = alertTime.size()+1;

        if (blocknumb>1){
            //get the rate in each block
            std::vector<double> vrate(blocknumb);
            int ith = 0;
            for (int ii=0;ii<blocknumb;ii++){
                //TTimeStamp tend = alertTime[ii];
                int nsum = 0;
                for (;ith<evtnumb;ith++){
                    if (ii<blocknumb-1){
                        if (m_evtTime[ith]>alertTime[ii]) break;
                    }
                    nsum++;
                }
                double dt = 0;
                if (ii==0) dt = alertTime[ii]-m_evtTime.front();
                else if (ii==blocknumb-1) dt = m_evtTime.back()-alertTime.back();
                else dt = alertTime[ii]- alertTime[ii-1];
                vrate[ii] = nsum/dt;
            }

            //check the change point
            for (int ii=blocknumb-2;ii>=0;ii--){
                if (m_evtTime.back()-alertTime[ii]>20){//time should be within 20s
                    break;
                }
                if (vrate[ii+1]-vrate[ii]<0){//rate should increase
                    continue;
                }
                b_isTriggered = true;
                //d_snTriggerTime = alertTime[ii].AsDouble();
                d_snTriggerTime = thist.AsDouble();
                ttrig->Fill();
                LogInfo<< "Find an alert!!!---[" << thist << " ]" <<std::endl;
                LogInfo<< "The change point is!!!---[" << alertTime[ii] << " ]" <<std::endl;
                break;
            }
        }
    }

    return true;
}

//static bool uniqueFcn(int i, int j){
//    return (i==j);
//}

int PromptMonitor::getNFiredPMT(){//here NFiredPMT means total number of hits
    double tbeg=100;// = This value should be changed when trigger window changes =
    double tend=100+d_T;
    // = First get the CdLpmtCalibEvt =
    JM::EvtNavigator *tnav=m_buf->curEvt();
    JM::CdLpmtCalibHeader* header_calib = JM::getHeaderObject<JM::CdLpmtCalibHeader>(tnav);
    if (!header_calib->hasEvent()){
        LogInfo<<"CdLpmtCalibEvt doesn't exist, skip it!"<<std::endl;
        return -1;
    }
    JM::CdLpmtCalibEvt* evt_calib = dynamic_cast<JM::CdLpmtCalibEvt*>(header_calib->event());
    const std::list<JM::CalibPmtChannel*>& l_pmtcol = evt_calib->calibPMTCol();
    int Npulse=0;// = Number of hits in (tbeg, tend) =
    int Ntot=0;// = Total number of hits =
    for (std::list<JM::CalibPmtChannel*>::const_iterator cit=l_pmtcol.begin();cit!=l_pmtcol.end();cit++){
        const std::vector<float>& ctime=(*cit)->time();
        Ntot += ctime.size();
        for (std::vector<float>::const_iterator tit=ctime.begin();tit!=ctime.end();++tit){
            if ((*tit)>tbeg && (*tit)<tend) Npulse++;
        }
    }
    return Npulse;
}

//int PromptMonitor::getNFiredPMTbyTruth(double gtTime){
//    //first get hit time and pmt id of this event
//    std::vector<double> m_hittime;
//    std::vector<int> m_PMTID;
//    JM::EvtNavigator *thisnav=m_buf->curEvt();
//    JM::ElecTruthHeader *headerElecTruth=dynamic_cast<JM::ElecTruthHeader*>(thisnav->getHeader("/Event/Sim/Truth"));
//    if (!headerElecTruth->hasLpmtTruth()){
//        LogWarn<<"can not get fired pmt number of LPMT!"<<std::endl;
//        return -1;
//    }
//    JM::LpmtElecTruthEvent *eventLpmtTruth=headerElecTruth->lpmtTruth();
//    std::vector<JM::LpmtElecTruth> lpmttruth=eventLpmtTruth->truths();
//    for (std::vector<JM::LpmtElecTruth>::iterator it=lpmttruth.begin();it!=lpmttruth.end();++it){
//        JM::LpmtElecTruth& lpmt = *it;
//        double hittime = lpmt.pulseHitTime().GetSeconds(); 
//        LogDebug<<"pmt hit time:"<<hittime<<std::endl;
//        m_hittime.push_back(hittime);
//        int pmtID = lpmt.pmtId();
//        m_PMTID.push_back(pmtID);
//    }
//
//    //get the number of fired pmts in time range d_T relative to gtTime
//    double itbeg=gtTime;
//    double itend=gtTime+d_T/1e9;
//    std::vector<double>::iterator ilow, iup;
//    ilow = std::lower_bound(m_hittime.begin(), m_hittime.end(), itbeg);
//    iup  = std::lower_bound(m_hittime.begin(), m_hittime.end(), itend);
//    int indexlow = std::distance(m_hittime.begin(), ilow);
//    int indexup  = std::distance(m_hittime.begin(), iup);
//
//    int npmts = std::distance(ilow, iup);
//    std::vector<int> ivecPMT(npmts);
//    std::vector<int>::iterator itpmt;
//    itpmt = std::unique_copy(m_PMTID.begin()+indexlow,m_PMTID.begin()+indexup,ivecPMT.begin());
//    std::sort(ivecPMT.begin(),itpmt);
//    itpmt = std::unique_copy(ivecPMT.begin(),itpmt,ivecPMT.begin(),uniqueFcn);
//    ivecPMT.resize(std::distance(ivecPMT.begin(),itpmt));
//
//    return ivecPMT.size();
//}

void PromptMonitor::initOutput(){
    i_totFiredPMTs = 0;
    i_evtType = 2;
    d_Qedep = 0;
    d_QedepX = 0;
    d_QedepY = 0;
    d_QedepZ = 0;
}

//void PromptMonitor::getEventUser(){
//    //get qedep from trackelectruth
//    JM::EvtNavigator *thisnav=m_buf->curEvt();
//    JM::ElecTruthHeader *headerElecTruth=dynamic_cast<JM::ElecTruthHeader*>(thisnav->getHeader("/Event/Sim/Truth"));
//    if (headerElecTruth==NULL){
//        LogWarn<<"elec truth header is not found!"<<std::endl;
//        d_Qedep=100;
//        d_QedepX=0;
//        d_QedepY=0;
//        d_QedepZ=0;
//        return;
//    }
//    if (!headerElecTruth->hasTrackTruth()){
//        LogWarn<<"can not get track truth!"<<std::endl;
//        return;
//    }
//    JM::TrackElecTruthEvent *eventTrackTruth=headerElecTruth->trackTruth();
//    const std::vector<JM::TrackElecTruth>& trktruth=eventTrackTruth->truths();
//    std::vector<JM::TrackElecTruth>* v_trackTruth=const_cast<std::vector<JM::TrackElecTruth>*>(&trktruth);
//    if (v_trackTruth->size()>=1){
//        d_Qedep=0;
//        for (std::vector<JM::TrackElecTruth>::iterator it=v_trackTruth->begin();it!=v_trackTruth->end();++it){
//            d_Qedep+=it->Qedep();
//        }
//        d_QedepX=v_trackTruth->at(0).initX();
//        d_QedepY=v_trackTruth->at(0).initY();
//        d_QedepZ=v_trackTruth->at(0).initZ();
//    }
//    else{
//        //for e+ sample, this case corresponds to after pulse
//        d_Qedep=100;
//        d_QedepX=0;
//        d_QedepY=0;
//        d_QedepZ=0;
//    }
//}

void PromptMonitor::generateRndVeto(double tbeg, double tend){
    LogInfo<< "generate muon events..." << std::endl;
    std::vector<double> m_muTime_tmp;
    int nveto = (tend-tbeg)*d_vetoRate;
    for(int ievt=0; ievt<nveto; ievt++){
        double itime = m_prnd->Uniform(tbeg, tend);
        //std::cout << "bkg time " << itime << std::endl;
        //vec_veto.push_back(itime);
        m_muTime_tmp.push_back(itime);
    }
    std::sort(m_muTime_tmp.begin(), m_muTime_tmp.end());

    //remove muon events within veto time
    LogInfo<< "remove mu-like events within veto time..." << std::endl;
    int nevts = m_muTime_tmp.size();
    for(int ievt=0; ievt<nevts;){
        double itime = m_muTime_tmp[ievt];
        m_muTime.push_back(itime);
        if(ievt<nevts-1){
            for(int jevt=ievt+1; jevt<nevts;jevt++){
                if(m_muTime_tmp[jevt]>(itime+d_vetoTime)){
                    ievt = jevt;
                    break;
                }
                if(jevt==nevts-1)ievt = jevt;
            }
        }
        else{
            ievt++;
        }
    }
}

void PromptMonitor::generateRndBkg(double tbeg, double tend){
    LogInfo<< "generate background events..." << std::endl;
    int nbkgs = (tend-tbeg)*d_bkgRate;
    for(int ievt=0; ievt<nbkgs; ievt++){
        double itime = m_prnd->Uniform(tbeg, tend);
        m_bkgTime.push_back(itime);
    }
    std::sort(m_bkgTime.begin(), m_bkgTime.end());

    //remove sn-like events within veto time
    LogInfo<< "number of SN-like events: " << m_bkgTime.size() << std::endl;
    for(int ievt=0;ievt<int(m_muTime.size());ievt++){
        double itbeg = m_muTime[ievt];
        double itend = itbeg+d_vetoTime;

        std::deque<double>::iterator ilow_sn, iup_sn;
        ilow_sn = std::lower_bound(m_bkgTime.begin(), m_bkgTime.end(), itbeg);
        iup_sn  = std::lower_bound(m_bkgTime.begin(), m_bkgTime.end(), itend);
        m_bkgTime.erase(ilow_sn, iup_sn);
    }
    LogInfo<< "After muon veto: " << m_bkgTime.size() << std::endl;
    for (double thist : m_bkgTime){
        std::cout<<thist<<"  ";
    }
    std::cout<<std::endl;
}
