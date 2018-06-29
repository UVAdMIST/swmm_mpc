# swmm_mpc 
`swmm_mpc` is a python package that can be used to perform model predictive control (MPC) for EPASWMM5 ([Environmental Protection Agency Stormwater Management Model](https://www.epa.gov/water-research/storm-water-management-model-swmm)). `swmm_mpc` relies on the [pyswmm package](https://github.com/OpenWaterAnalytics/pyswmm) which enables the step by step running of SWMM5 models through Python.  

# Installation
## 1. Install swmm_mpc
```
git clone https://github.com/uva-hydroinformatics/swmm_mpc.git
pip install swmm_mpc/
```
## 2. Install pyswmm
swmm\_mpc requires a special version of OWA's pyswmm. To install this do:

```
pip install git+git://github.com/uva-hydroinformatics/pyswmm.git@feature_save_hotstart
```

## 3. Install EPASWMM5 
You will also need to have a working version of EPASWMM5 on your machine and have it added to the path. You can download the source code from the [EPA Website](https://www.epa.gov/water-research/storm-water-management-model-swmm). In Linux you can do this as follows:
```
wget https://www.epa.gov/sites/production/files/2017-03/swmm51012_engine_2.zip
unzip swmm51012_engine_2.zip -d swmm5
cd swmm5/
unzip sources5_1_012.zip -d src
unzip makefiles.zip -d mk
cd mk
unzip GNU-CLE.zip -d gnu
cp gnu/Makefile ../src/
cd ../src
```
Then follow the instructions editing the swmm5.c line to read:
```
#define CLE
\\#define SOL
\\#define DLL
```
Then do
```
make
```
To add to the path, add this line to your .bashrc
```
export PATH="/path/to/swmm5/src:$PATH"
```

