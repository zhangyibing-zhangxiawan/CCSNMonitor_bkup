#include "SNClassTool.h"
#include "Event/SNHeader.h"
#include "SniperKernel/ToolFactory.h"
#include "SniperKernel/SniperDataPtr.h"
#include "EvtNavigator/EvtNavHelper.h"
#include "TMath.h"

DECLARE_TOOL(SNClassTool);

SNClassTool::SNClassTool(const std::string &name): ToolBase(name){
    declProp("maxN", i_maxN=2);
    declProp("dT", i_dT);
}

SNClassTool::~SNClassTool(){
}

bool SNClassTool::initialize(){
    LogInfo<<"Initializing SN classification tool..."<<std::endl;
    // = Get the event buffer =
    SniperDataPtr<JM::NavBuffer> navbuf(getRoot(), "/Event");
    if (navbuf.invalid()){
        LogError<<"can not get navbuffer!!!"<<std::endl;
        return false;
    }
    m_buf=navbuf.data();
    return true;
}

bool SNClassTool::finalize(){
    return true;
}

bool SNClassTool::isVetoed(JM::NavBuffer::Iterator navit){
    //To be added in the future
    return false;
}

bool SNClassTool::findCorrelation(JM::NavBuffer::Iterator navit, std::vector<JM::OecEvt*>& vcorEvts){
    if (vcorEvts.size()!=1){
        LogError<<"Current event is not pushed"<<std::endl;
        return false;
    }
    const TTimeStamp& thisTime=vcorEvts.at(0)->getTime();
    for (JM::NavBuffer::Iterator tmpit=++navit;tmpit!=m_buf->end();++tmpit){
        JM::OecHeader* aHeaderOEC = JM::getHeaderObject<JM::OecHeader>(tmpit->get());
        JM::OecEvt *aEventOEC = dynamic_cast<JM::OecEvt*>(aHeaderOEC->event("JM::OecEvt"));
        const TTimeStamp& afterTime=aEventOEC->getTime();
        double dt=(afterTime-thisTime)*1e9;
        if (dt>i_dT) break;
        if (this->isVetoed(tmpit)) continue;
        vcorEvts.push_back(aEventOEC);
    }
    int totEvts = vcorEvts.size();
    //LogInfo<<"TEST IN SNClassTool!!!!!! i_maxN="<<i_maxN<<std::endl;//i_maxN=100
    if (totEvts>i_maxN){
        LogWarn<<totEvts<<" Multiple tags!"<<std::endl;
        return false;
    }
    if (totEvts==1){
        LogInfo<<"No correlated events!"<<std::endl;
        return false;
    }
    return true;
}

bool SNClassTool::calClassifyQuantity(const std::vector<JM::OecEvt*>& corEvents){
    // = For SN IBD selection =
    int totEvts = corEvents.size();
    if (totEvts<2) return false;
    m_eventPair.clear();
    m_classQuantity.clear();

    classifyQuantity thecondition = classifyQuantity({"penergy", "denergy", "distance", "deltaT", "rCut"});
    JM::OecEvt *tEvent = corEvents.at(0);
    double tvtxX=tEvent->getVertexX();
    double tvtxY=tEvent->getVertexY();
    double tvtxZ=tEvent->getVertexZ();
    double tr = TMath::Sqrt(tvtxX*tvtxX+tvtxY*tvtxY+tvtxZ*tvtxZ);
    for (int ii=1;ii<totEvts;ii++){  
        JM::OecEvt *aEvent = corEvents.at(ii);
        double dvtxX=aEvent->getVertexX();
        double dvtxY=aEvent->getVertexY();
        double dvtxZ=aEvent->getVertexZ();
        double dr = TMath::Sqrt(dvtxX*dvtxX+dvtxY*dvtxY+dvtxZ*dvtxZ);
        double dx=tvtxX-dvtxX;
        double dy=tvtxY-dvtxY;
        double dz=tvtxZ-dvtxZ;
        float dist=TMath::Sqrt(dx*dx+dy*dy+dz*dz);
        float dT=1e9*(aEvent->getTime()-tEvent->getTime());
        float penergy=tEvent->getEnergy();
        float denergy=aEvent->getEnergy();
        float rcut = tr>dr ? tr : dr;
  
        thecondition.setValue("penergy", penergy);
        thecondition.setValue("denergy", denergy);
        thecondition.setValue("distance", dist);
        thecondition.setValue("deltaT", dT);
        thecondition.setValue("rCut", rcut);
        m_eventPair.push_back(std::make_pair(tEvent, aEvent));
        m_classQuantity.push_back(thecondition);
		
    }
    return true;
}

bool SNClassTool::userFunc(JM::EvtNavigator* thisnav, const EventPair& thispair){
    //first get SNHeader to check if it exist
    JM::SNHeader *tHeaderSN=dynamic_cast<JM::SNHeader*>(thisnav->getHeader("/Event/SN"));
    if (tHeaderSN!=NULL) return true;

    JM::OecEvt *tEventOEC = thispair.first;
    JM::OecEvt *aEventOEC = thispair.second;

    //if SNHeader does not exist, create it
    JM::SNEvent *tEventSN=new JM::SNEvent();
    tEventSN->setPromptE(tEventOEC->getEnergy());
    tEventSN->setPromptX(tEventOEC->getVertexX());
    tEventSN->setPromptY(tEventOEC->getVertexY());
    tEventSN->setPromptZ(tEventOEC->getVertexZ());
    TTimeStamp ptime=tEventOEC->getTime();
    tEventSN->setPromptTime(ptime);

    tEventSN->setDelayedE(aEventOEC->getEnergy());
    tEventSN->setDelayedX(aEventOEC->getVertexX());
    tEventSN->setDelayedY(aEventOEC->getVertexY());
    tEventSN->setDelayedZ(aEventOEC->getVertexZ());
    TTimeStamp dtime=aEventOEC->getTime();
    tEventSN->setDelayedTime(dtime);
    //==============
    tHeaderSN=new JM::SNHeader();
    tHeaderSN->setEvent(tEventSN);
    JM::addHeaderObject(thisnav, tHeaderSN);
    //thisnav->addHeader("/Event/SN", tHeaderSN);
    return true;
}
