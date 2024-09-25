#include "readSNEvt/readSNEvt.h"
#include "SniperKernel/AlgFactory.h"
#include "Event/SNHeader.h"
#include "RootWriter/RootWriter.h"

DECLARE_ALGORITHM(readSNEvt);
readSNEvt::readSNEvt(const std::string& name): AlgBase(name), m_snEvt(NULL){
}

readSNEvt::~readSNEvt(){
}

bool readSNEvt::initialize(){
    //get the buffer
    SniperDataPtr<JM::NavBuffer> navBuf(getRoot(), "/Event");
    if ( navBuf.invalid() ) {
        LogError << "cannot get the NavBuffer @ /Event" << std::endl;
        return false;
    }
    m_buf = dynamic_cast<JM::NavBuffer*>(navBuf.data());

    //Get rootwriter and create the tree
    SniperPtr<RootWriter> rwsvc(getParent(),"RootWriter");
    if ( rwsvc.invalid() ) {
        LogError << "cannot get the rootwriter service." << std::endl;
        return false;
    }
    m_snEvt = rwsvc->bookTree(*getParent(), "USER_PRESN/evt", "preSN");
    m_snEvt->Branch("t", &d_time, "t/D");
    return true;
}

bool readSNEvt::execute(){
    //==================get the current event================
    JM::EvtNavigator* tnav=m_buf->curEvt();
    JM::SNHeader *tHeaderSN=dynamic_cast<JM::SNHeader*>(tnav->getHeader("/Event/SN"));
    if (tHeaderSN==NULL){
        LogDebug<<"Not an SN event!Skip!!"<<std::endl;
        return true;
    }
    JM::SNEvent *tEventSN=dynamic_cast<JM::SNEvent*>(tHeaderSN->event("JM::SNEvent"));
    LogInfo<<"Find an IBD: "<<tEventSN->getPromptTime()<<"    "<<tEventSN->getDelayedTime()<<std::endl;

    d_time = tEventSN->getPromptTime().AsDouble();
    m_snEvt->Fill();
    return true;
}

bool readSNEvt::finalize(){
    return true;
}
