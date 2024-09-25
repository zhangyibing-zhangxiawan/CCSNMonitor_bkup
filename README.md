# **CCSNMonitor**
To give alert on the future CCSN

## **Setup the environment and build**
* Setup JUNO offline env
    * source setup_juno.sh
* Build the code:
    * Change the path in "build.sh" into YOURINSTALLAREA
    * mkdir build
    * ./build.sh
* Setup the env for CCSNMonitor
    * source ${yourPath}/InstallArea/setup.sh

## **Analysis**
Some analysis code:
* **calFAR.py, drawFAR.ipynb**: to calculate the false alert rate for 'sliding-window' and 'bayesian-block' methods

## **MonitorMethod**
The methods can be used by CCSN monitor:
* **Sliding window**
* **Time interval**
* **Bayesian block**

## **PromptMonitor**
### Discriptions
* The CCSN monitor which will be performed at FPGA.

### Some options
* --npmtcut_low, --npmtcut_high: The cut used to select sn-like events
* --useToyBKG: Generate toy backgrounds
* --useToyMuon: Generate toy muons
* --Method: Specify the monitor method to be used

## **OnlineMonitor**
### Discriptions
* The CCSN monitor which will be performed at DAQ
* It is based on the OEC frame-work
    * First, using OEC to select SN and pre-SN candidates (IBD)
    * Then, perform the monitoring algorithms

### Some options
* **For details, refer to the python script run.py**
* Regarding to the random background
    * --seed: Seed for random numbers
    * --enableSNtoybkg, disableSNtoybkg: Whether to generate toy background for SN or not. Toy background is generated using uniform distribution according to the background rate, where muon is not included
    * --enablePretoybkg, --disablePretoybkg: Whether to generate toy background for pre-SN or not.
* Options in online monitor, common for SN monitor and pre-SN monitor
    * --monitorMethod: The algorithm used to find alert
    * --enableSpecifiedStart, --disableSpecifiedStart: Whether to specify the time of start. If true, the start time is given by "--beginTime"; If false, the start time is the time of the first signal (not background).
    * --beginTime: The time when to start the online monitor.
* Options for the monitor algorithms
    * --sn-T, --sn-Nthr, --sn-startTime, --sn-dT: For sliding window method. Substitute "sn" by "presn" to specify the corresponding options for pre-SN monitor.
    * --sn-T, --sn-Nthr, --sn-startTime: For time interval method (sliding event method).
    * --sn-ncp: For Bayesian block method.