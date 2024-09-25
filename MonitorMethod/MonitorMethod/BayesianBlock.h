#ifndef BAYESIANBLOCK_H
#define BAYESIANBLOCK_H
#include "MonitorMethod/IMonitorMethod.h"
#include "SniperKernel/ToolBase.h"

class BayesianBlock: public ToolBase, public IMonitorMethod{
    public:
        BayesianBlock(const std::string&);
        ~BayesianBlock();

        struct PAR{
            int maxN;//maximum number of events used by this method
            double ncp_prior;
            PAR(){
            }
            void print(){
                std::cout<<"The maximum number of events used:"<<maxN<<std::endl;
                std::cout<<"The Bayesian block parameter:"<<ncp_prior<<std::endl;
            }
        };

        virtual bool init();
        virtual bool fina();
        virtual std::deque<TTimeStamp> findAlert(const std::deque<TTimeStamp>&);

        void setPar(PAR&);
        const PAR &getPar(){return m_par;}

    private:
        PAR m_par;
        int i_maxN;
        double d_ncp;
};
#endif
