#ifndef SNCLASSTOOL_H
#define SNCLASSTOOL_H
#include "HECAlg/IClassTool.h"
#include "SniperKernel/ToolBase.h"

class SNClassTool: public ToolBase, public IClassTool{
    public:
        SNClassTool(const std::string&);
        ~SNClassTool();

        // = Inherite from ToolBase =
        virtual bool initialize();
        virtual bool finalize();

        // = Inherite from IClassTool =
        virtual bool isVetoed(JM::NavBuffer::Iterator);//True:the event is vetoed    False:the event is not vetoed
        virtual bool findCorrelation(JM::NavBuffer::Iterator, std::vector<JM::OecEvt*>&);//Find the events correlated to this event
        virtual bool calClassifyQuantity(const std::vector<JM::OecEvt*>&);//Input:the events correlated in time
        virtual bool userFunc(JM::EvtNavigator*, const EventPair&);

    private:
        JM::NavBuffer *m_buf;
        // = Parameters used by this tool =
        int i_maxN;// = The max number of correlated events =
        int i_dT;// = The max time for two events to be correlated;Unit: ns
};
#endif
