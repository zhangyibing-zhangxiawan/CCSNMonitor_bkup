#include "OnlineMonitor.h"
#include "SNMonitor.h"
#include "preSNMonitor.h"
#include "Event/SNHeader.h"
#include "MonitorMethod/SlidingWindow.h"
#include "MonitorMethod/TimeInterval.h"
#include "MonitorMethod/BayesianBlock.h"
#include "SniperKernel/AlgFactory.h"
#include "EvtNavigator/EvtNavHelper.h"
#include "RootWriter/RootWriter.h"

DECLARE_ALGORITHM(OnlineMonitor);

OnlineMonitor::OnlineMonitor(const std::string &name): AlgBase(name){
    m_status = MonitorStatus::noAlert;
    m_SNMonitor = new SNMonitor();
    m_preSNMonitor = new preSNMonitor;

    //For the result output
    m_treeSN = NULL;
    m_treepreSN = NULL;
    d_alertTime = 0;
    d_dirx = 0;
    d_diry = 0;
    d_dirz = 0;

    declProp("specifyBeginTime", b_specifyBeginTime_sn=true);
    declProp("beginTime", d_tbeg=0);
    declProp("useToyBkg_sn", b_sntoybkg=true);
    declProp("useToyBkg_pre", b_pretoybkg=false);
    declProp("seed", i_seed=0);
    m_rnd = NULL;
}

OnlineMonitor::~OnlineMonitor(){
    delete m_SNMonitor;
    delete m_preSNMonitor;
    if (m_rnd!=NULL) delete m_rnd;
}

bool OnlineMonitor::initialize(){
    LogInfo<<"initializing OnlineMonitor..."<<std::endl;

    //set start time
    b_specifyBeginTime_presn = b_specifyBeginTime_sn;
    if (b_specifyBeginTime_sn){
        int sec = int(d_tbeg);
        int nanosec = int((d_tbeg-sec)*1e9);
        TTimeStamp begtime = TTimeStamp(sec, nanosec);
        m_SNMonitor->setBeginTime(begtime);
        m_preSNMonitor->setBeginTime(begtime);
    }

    //set the monitor method
    IMonitorMethod *thistool = tool<IMonitorMethod>("sn");
    if (!thistool->init()){
        LogError<<"Error when initializing the tool:"<<dynamic_cast<ToolBase*>(thistool)->tag()<<std::endl;
        return false;
    }
    m_SNMonitor->setMethod(thistool);
    thistool = tool<IMonitorMethod>("presn");
    if (!thistool->init()){
        LogError<<"Error when initializing the tool:"<<dynamic_cast<ToolBase*>(thistool)->tag()<<std::endl;
        return false;
    }
    m_preSNMonitor->setMethod(thistool);

    //set the toy option
    m_rnd = new TRandom3(i_seed);
    //if (b_sntoybkg || b_pretoybkg) m_rnd = new TRandom3(i_seed);
    if (b_sntoybkg){
        m_SNMonitor->useToyBkg();// void useToyBkg(){b_toyBkg=true;}
    }
    else m_SNMonitor->disableToyBkg();
    m_SNMonitor->setRndGen(m_rnd);//void setRndGen(TRandom3* rnd){m_rnd=rnd;}
    m_SNMonitor->useToyMuon();//void useToyMuon(){b_toyMuon=true;}
    if (b_pretoybkg){
        m_preSNMonitor->useToyBkg();
    }
    else m_preSNMonitor->disableToyBkg();
    m_preSNMonitor->setRndGen(m_rnd);
    m_preSNMonitor->useToyMuon();

    //get the buffer
    SniperDataPtr<JM::NavBuffer> navBuf(getRoot(), "/Event");
    if ( navBuf.invalid() ) {
        LogError << "cannot get the NavBuffer @ /Event" << std::endl;
        return false;
    }
    m_buf = dynamic_cast<JM::NavBuffer*>(navBuf.data());

    //initialize the output
    SniperPtr<RootWriter> rwsvc(getParent(),"RootWriter");
    if ( rwsvc.invalid() ) {
        LogError << "cannot get the rootwriter service." << std::endl;
        return false;
    }
    m_treeSN = rwsvc->bookTree(*getParent(), "USER_SN/alert_sn", "SN");
    m_treeSN->Branch("alertStatus", &m_status, "alertStatus/I");
    m_treeSN->Branch("alertTime", &d_alertTime, "alertTime/D");
    m_treeSN->Branch("dirx", &d_dirx, "dirx/D");
    m_treeSN->Branch("diry", &d_diry, "diry/D");
    m_treeSN->Branch("dirz", &d_dirz, "dirz/D");
    m_treepreSN = rwsvc->bookTree(*getParent(), "USER_PRESN/alert_presn", "preSN");
    m_treepreSN->Branch("alertStatus", &m_status, "alertStatus/I");
    m_treepreSN->Branch("alertTime", &d_alertTime, "alertTime/D");
    m_treepreSN->Branch("dirx", &d_dirx, "dirx/D");
    m_treepreSN->Branch("diry", &d_diry, "diry/D");
    m_treepreSN->Branch("dirz", &d_dirz, "dirz/D");
    return true;
}

bool OnlineMonitor::finalize(){
    //Finalize the monitoring method
    IMonitorMethod *thistool = tool<IMonitorMethod>("sn");
    if (!thistool->fina()){
        LogError<<"Error when finalizing the tool:"<<dynamic_cast<ToolBase*>(thistool)->tag()<<std::endl;
        return false;
    }
    thistool = tool<IMonitorMethod>("presn");
    if (!thistool->fina()){
        LogError<<"Error when finalizing the tool:"<<dynamic_cast<ToolBase*>(thistool)->tag()<<std::endl;
        return false;
    }

    //Finalize the output
    return true;
}

bool OnlineMonitor::execute(){
    //==================get the current OecEvt================
    JM::EvtNavigator* tnav=m_buf->curEvt();
    JM::OecHeader* tHeaderOEC = JM::getHeaderObject<JM::OecHeader>(tnav);
    JM::OecEvt *tEventOEC=dynamic_cast<JM::OecEvt*>(tHeaderOEC->event("JM::OecEvt"));

    //==================get the SNEvent================
    JM::SNHeader* tHeaderSN = JM::getHeaderObject<JM::SNHeader>(tnav);
    if (tHeaderSN==NULL){
        LogDebug<<"Not an SN event!Skip!!"<<std::endl;
        return true;
    }
    JM::SNEvent *tEventSN=dynamic_cast<JM::SNEvent*>(tHeaderSN->event("JM::SNEvent"));
    std::string IBDType=getEventType(tEventOEC);
    LogInfo<<"Find an IBD of type "<<IBDType<<": "<<tEventSN->getPromptTime()<<"    "<<tEventSN->getDelayedTime()<<std::endl;

    if (!IBDType.compare("unknow") || !IBDType.compare("mix")) return true;
    else if (!IBDType.compare("sn")){
        m_SNMonitor->cache(tEventSN);
        m_SNMonitor->add(tEventSN->getPromptTime());
        if (!b_specifyBeginTime_sn){//set the begin time to be the first signal
            m_SNMonitor->setBeginTime(tEventSN->getPromptTime());
            b_specifyBeginTime_sn = true;
            LogInfo<<"Begin time for sn is set:"<<tEventSN->getPromptTime()<<std::endl;
            //Set the current time for the sliding-window or time-interval method
            IMonitorMethod *thistool = tool<IMonitorMethod>("sn");
            std::string methodname = dynamic_cast<ToolBase*>(thistool)->tag();
            if (!methodname.compare("SlidingWindow")){
                dynamic_cast<SlidingWindow*>(thistool)->setCurTime(tEventSN->getPromptTime());
            }
            else if (!methodname.compare("TimeInterval")){
                dynamic_cast<TimeInterval*>(thistool)->setCurTime(tEventSN->getPromptTime());
            }
        }
    }
    else if (!IBDType.compare("pre-sn")){
        m_preSNMonitor->cache(tEventSN);
        m_preSNMonitor->add(tEventSN->getPromptTime());
        if (!b_specifyBeginTime_presn){//set the begin time to be the first signal
            m_preSNMonitor->setBeginTime(tEventSN->getPromptTime());
            b_specifyBeginTime_presn = true;
            LogInfo<<"Begin time for presn is set:"<<tEventSN->getPromptTime()<<std::endl;
            //Set the current time for the sliding-window or time-interval method
            IMonitorMethod *thistool = tool<IMonitorMethod>("presn");
            std::string methodname = dynamic_cast<ToolBase*>(thistool)->tag();
            if (!methodname.compare("SlidingWindow")){
                dynamic_cast<SlidingWindow*>(thistool)->setCurTime(tEventSN->getPromptTime());
            }
            else if (!methodname.compare("TimeInterval")){
                dynamic_cast<TimeInterval*>(thistool)->setCurTime(tEventSN->getPromptTime());
            }
        }
        m_SNMonitor->cache(tEventSN);
    }
    else if (!IBDType.compare("other")){
        m_SNMonitor->cache(tEventSN);
    }

    MonitorMessage snmessage = m_SNMonitor->monitor(m_status);//virtual MonitorMessage monitor(MonitorStatus&) = 0;
    if (snmessage == MonitorMessage::newAlert){
        TTimeStamp alertt = m_SNMonitor->getAlertTime();
        LogInfo<<"Find a new alert of type "<<m_status<<" at:"<<alertt<<std::endl;
        //TVector3 alertdir = m_SNMonitor->getDirection();
        //LogInfo<<"The direction is calcualted to be:("<<alertdir.X()<<", "<<alertdir.Y()<<", "<<alertdir.Z()<<")"<<std::endl;
        d_alertTime = alertt.AsDouble();
        d_dirx = 0;
        d_diry = 0;
        d_dirz = 0;
        m_treeSN->Fill();
    }
    else if (snmessage == MonitorMessage::newDirection){
        TTimeStamp alertt = m_SNMonitor->getAlertTime();
        TVector3 alertdir = m_SNMonitor->getDirection();
        LogInfo<<"The direction has been updated:("<<alertdir.X()<<", "<<alertdir.Y()<<", "<<alertdir.Z()<<")"<<std::endl;
        d_alertTime = alertt.AsDouble();
        d_dirx = alertdir.X();
        d_diry = alertdir.Y();
        d_dirz = alertdir.Z();
        m_treeSN->Fill();
    }
    MonitorMessage premessage = m_preSNMonitor->monitor(m_status);
    if (premessage == MonitorMessage::newAlert){
        TTimeStamp alertt = m_preSNMonitor->getAlertTime();
        LogInfo<<"Find a new alert "<<m_status<<" at:"<<alertt<<std::endl;
        //TVector3 alertdir = m_preSNMonitor->getDirection();
        //LogInfo<<"The direction is calcualted to be:("<<alertdir.X()<<", "<<alertdir.Y()<<", "<<alertdir.Z()<<")"<<std::endl;
        d_alertTime = alertt.AsDouble();
        d_dirx = 0;
        d_diry = 0;
        d_dirz = 0;
        m_treepreSN->Fill();
    }
    else if (premessage == MonitorMessage::newDirection){
        TTimeStamp alertt = m_preSNMonitor->getAlertTime();
        TVector3 alertdir = m_preSNMonitor->getDirection();
        LogInfo<<"The direction has been updated:("<<alertdir.X()<<", "<<alertdir.Y()<<", "<<alertdir.Z()<<")"<<std::endl;
        d_alertTime = alertt.AsDouble();
        d_dirx = alertdir.X();
        d_diry = alertdir.Y();
        d_dirz = alertdir.Z();
        m_treepreSN->Fill();
    }

    return true;
}

std::string OnlineMonitor::getEventType(JM::OecEvt *thisEvent){
    //pre-sn IBD:   0x00000001, 0x00000002
    //sn IBD:       0x00000010, 0x00000020
    //other IBD:    0x00000100, 0x00000200
    std::string thisType="unknow";
    int tTag=thisEvent->getTag();
    LogInfo<<"Attention here!!!!!!Test point1!!!!!!!!!!!!!!!!!!!"<<tTag<<std::endl;
    tTag=tTag<<20;
    tTag=tTag>>20;
    LogInfo<<"Attention here!!!!!!Test point2!!!!!!!!!!!!!!!!!!!"<<tTag<<std::endl;
    if      (tTag==0x001) {thisType="pre-sn";LogInfo<<"Attention here thisType=pre-sn!!!!!!!!!!!"<<std::endl;}
    else if (tTag==0x010) {thisType="sn";LogInfo<<"Attention here thisType=sn!!!!!!!!!!!"<<std::endl;}
    else if (tTag==0x100) {thisType="other";LogInfo<<"Attention here thisType=other!!!!!!!!!!!"<<std::endl;}
    else if (tTag==0x011) {thisType="both";LogInfo<<"Attention here thisType=both!!!!!!!!!!!"<<std::endl;}
    else if (tTag==0x030) {thisType="mix";LogInfo<<"Attention here thisType=mix!!!!!!!!!!!"<<std::endl;}
    return thisType;
}
