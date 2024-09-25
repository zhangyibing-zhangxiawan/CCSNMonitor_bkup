void example_bayesian(){
    TFile* infile = TFile::Open("/junofs/users/huangx/myProject/CCSNMonitor/PromptMonitor/myJob/result/sn_intp3003.data/1/110/BayesianBlock/ncp9.3/promptTrigger_1.root", "READ");
    TTree* t_evt = dynamic_cast<TTree*>(infile->Get("tevt"));
    int i_evttype = 0;
    double d_time = 0;
    t_evt->SetBranchAddress("evtType", &i_evttype);
    t_evt->SetBranchAddress("time", &d_time);
    //sn-like: 0
    int totevts = t_evt->GetEntries();
    for (int i=0;i<totevts;i++){
        t_evt->GetEntry(i);
        if (i_evttype!=0) continue;
    }
}
