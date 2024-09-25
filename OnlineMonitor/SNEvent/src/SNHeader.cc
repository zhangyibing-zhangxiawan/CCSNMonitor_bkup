#include "Event/SNHeader.h"

ClassImp(JM::SNHeader);

namespace JM{
    SNHeader::SNHeader(){
    }

    SNHeader::~SNHeader(){
    }

    EventObject* SNHeader::event(const string &value){
        if (value=="JM::SNEvent"){
            return m_event.GetObject();
        }
        return NULL;
    }
    void SNHeader::setEventEntry(const string &eventName, Long64_t &value){
        if (eventName=="JM::SNEvent"){
            m_event.setEntry(value);
        }
    }
}
