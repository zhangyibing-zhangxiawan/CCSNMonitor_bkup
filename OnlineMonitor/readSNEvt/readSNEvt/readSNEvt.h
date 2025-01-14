#ifndef READSNEVT_H
#define READSNEVT_H
#include "SniperKernel/AlgBase.h"
#include "EvtNavigator/NavBuffer.h"
#include "TTree.h"

class readSNEvt: public AlgBase{
    public:
        readSNEvt(const std::string&);
        ~readSNEvt();

        bool initialize();
        bool execute();
        bool finalize();

    private:
        JM::NavBuffer *m_buf;

        //The output
        TTree* m_snEvt;
        double d_time;
};
#endif
