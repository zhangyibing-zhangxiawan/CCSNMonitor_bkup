#ifndef SNHEADER_H
#define SNHEADER_H

#include "Event/HeaderObject.h"
#include "EDMUtil/SmartRef.h"
#include "SNEvent.h"

using namespace std;

namespace JM{
    class SNHeader:public HeaderObject{
        public:
            SNHeader();
            ~SNHeader();

            //virtual function
            EventObject *event(const string &value);
            void setEventEntry(const string &eventName, Long64_t &value);
            
            void setEvent(SNEvent* value){m_event=value;}


        private:
            JM::SmartRef m_event;

        public:
            ClassDef(SNHeader,2)
    };
}

#endif
