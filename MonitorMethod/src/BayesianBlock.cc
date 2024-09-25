#include "MonitorMethod/BayesianBlock.h"
#include "SniperKernel/ToolFactory.h"
#include "TMath.h"

DECLARE_TOOL(BayesianBlock);

BayesianBlock::BayesianBlock(const std::string &name): ToolBase(name){
    declProp("maxN", i_maxN=1000);
    declProp("ncp_prior", d_ncp=7.0);
}

BayesianBlock::~BayesianBlock(){
}

bool BayesianBlock::init(){
    m_par.maxN = i_maxN;
    m_par.ncp_prior = d_ncp;
    m_par.print();
    return true;
}

bool BayesianBlock::fina(){
    return true;
}

std::deque<TTimeStamp> BayesianBlock::findAlert(const std::deque<TTimeStamp> &vEvtTime){
    //the first and last event of vEvtTime is not included in vAlertTime
    std::deque<TTimeStamp> vAlertTime;
    vAlertTime.clear();
    const int vsize = vEvtTime.size();
    if (vsize<2){
        LogWarn<<"There are less than 2 events, no change points are found!"<<std::endl;
        return vAlertTime;
    }
    if (vsize<m_par.maxN){
        LogWarn<<"There are not enough events:"<<vEvtTime.size()<<"<"<<m_par.maxN<<std::endl;
    }

    //get the time length of this event
    std::vector<double> vT;//from (t_(i-1)+t_i)/2 to (t_i+t_(i+1))/2
    vT.push_back((vEvtTime.at(1)-vEvtTime.at(0))/2.);
    for (int i=1;i<vsize-1;i++){
        double dt = vEvtTime.at(i+1)-vEvtTime.at(i-1);
        dt/=2.;
        vT.push_back(dt);
    }
    vT.push_back((vEvtTime.at(vsize-1)-vEvtTime.at(vsize-2))/2.);

    std::vector<double> vBestLH;//the likelihood of the first ii events
    std::vector<int> vLast;//the event corresponding to the first event in last block
    vBestLH.push_back(1*(log(1/vT.at(0)))-m_par.ncp_prior);
    vLast.push_back(0);
    for (int ii=1;ii<vsize;ii++){
        //get the best block of first ii+1 events
        double bestlh = -10000000;
        int bestlast = 0;
        for (int jj=ii;jj>=0;jj--){
            //assuming the first event in last block is jjth event
            double tsum = 0;
            int nsum = 0;
            for (int kk=ii;kk>=jj;kk--){
                nsum++;
                tsum += vT.at(kk);
            }
            double thislh = 0;
            thislh += nsum*(log(nsum/tsum))-m_par.ncp_prior;
            if (jj==0) thislh += 0;
            else thislh += vBestLH.at(jj-1);
            if (thislh>bestlh){
                bestlh = thislh;
                bestlast = jj;
            }
        }
        vBestLH.push_back(bestlh);
        vLast.push_back(bestlast);
    }
    ////print the vBestLH for checking
    //for(double bestlh : vBestLH){
    //    std::cout<<bestlh<<"  ";
    //}
    //std::cout<<std::endl;

    //get the change points
    int ii = vsize-1;
    while (ii>=0){
        int icp = vLast.at(ii);
        if (icp==0){
            //vAlertTime.push_front(vEvtTime[0]);
        }
        //else if (icp==vsize-1){
        //    vAlertTime.push_front(vEvtTime[vsize-1]);
        //}
        else{
            TTimeStamp t1 = vEvtTime.at(icp-1);
            TTimeStamp t2 = vEvtTime.at(icp);
            double dt = t2-t1;
            dt/=2.;
            int sec = int(dt);
            int nanosec =int(1e9*(dt-sec));
            t1.Add(TTimeStamp(sec, nanosec));
            vAlertTime.push_front(t1);
        }
        ii = icp-1;
    }
    //print the change points for checking
    LogDebug<<"The change points: ";
    for(TTimeStamp cp : vAlertTime){
        LogDebug<<cp<<"  ";
    }
    LogDebug<<std::endl;

    return vAlertTime;
}

void BayesianBlock::setPar(PAR &thepar){
    m_par.maxN = thepar.maxN;
    m_par.ncp_prior = thepar.ncp_prior;
    m_par.print();
}
