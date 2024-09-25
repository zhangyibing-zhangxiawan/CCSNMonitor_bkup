#ifndef TIMEINTERVAL_H
#define TIMEINTERVAL_H
#include "MonitorMethod/IMonitorMethod.h"
#include "SniperKernel/ToolBase.h"

class TimeInterval: public ToolBase, public IMonitorMethod{
    public:
        TimeInterval(const std::string&);
        ~TimeInterval();

        struct PAR{
            TTimeStamp curTime;//the time of latest event been used
            double T;//unit:s, when t_nthr<T, give the alert
            int Nthr;//the number of events (Nthr+1) to calculate the time interval
            PAR(){
                curTime = TTimeStamp(0, 0);
                T = 10;
                Nthr = 3;
            }
            void print(){
                std::cout<<"The number of events used to get time interval:"<<Nthr<<std::endl;
                std::cout<<"The threshold of time interval of Nthr+1 events:"<<T<<std::endl;
            }
        };

        virtual bool init();
        virtual bool fina();
        virtual std::deque<TTimeStamp> findAlert(const std::deque<TTimeStamp>&);

        void setCurTime(const TTimeStamp&);
        void setPar(PAR&);
        const PAR &getPar(){return m_par;}

    private:
        PAR m_par;
        double d_T;
        double d_tbeg;
        int i_Nthr;
};
#endif
