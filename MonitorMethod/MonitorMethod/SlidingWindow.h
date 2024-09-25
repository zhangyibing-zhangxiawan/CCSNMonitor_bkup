#ifndef SLIDINGWINDOW_H
#define SLIDINGWINDOW_H
#include "MonitorMethod/IMonitorMethod.h"
#include "SniperKernel/ToolBase.h"

class SlidingWindow: public ToolBase, public IMonitorMethod{
    public:
        SlidingWindow(const std::string&);
        ~SlidingWindow();

        struct PAR{
            TTimeStamp curTime;//the current end of time window
            TTimeStamp slideT;//the length of the window
            TTimeStamp freshT;//the step of each slide
            int Nthr;//when N_in_window > i_Nthr, give the alert
            PAR(){
                curTime = TTimeStamp(0, 0);
                slideT = TTimeStamp(0, 4000000);
                freshT = TTimeStamp(0, 1000000);
                Nthr = 3;
            }
            void print(){
                std::cout<<"The length of the time window:"<<slideT.AsDouble()<<std::endl;
                std::cout<<"The step of each slide:"<<freshT.AsDouble()<<std::endl;
                std::cout<<"The threshold of number of events in the time window:"<<Nthr<<std::endl;
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
        double d_slideT;
        double d_freshT;
        double d_tbeg;
        int i_Nthr;
};
#endif
