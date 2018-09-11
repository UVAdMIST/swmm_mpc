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

# Usage
The `run_swmm_mpc` function is the main function (maybe the only function) that 
you will likely use. Here is an example of how I use it. First I write a small 
script to indicate the model and the different parameters I want to use, like 
this (called `my_swmm_mpc.py` in the next step):

```python
from swmm_mpc.swmm_mpc import run_swmm_mpc

inp_file = "/home/jms3fb/research/sadler4/paper_4/test_models/models/simple_2_ctl_smt.inp"
control_horizon = 1. #hr
control_time_step = 900. #sec
control_str_ids = ["ORIFICE R1", "ORIFICE R2"]
results_dir = "/home/jms3fb/research/sadler4/paper_4/data/results/"
work_dir = "/home/jms3fb/research/work/"
ngen = 4
nindividuals = 300

# target_depth_dict={'St1':{'target':1, 'weight':0.1}, 'St2':{'target':1.5, 'weight':0.1}}



def main():
    run_swmm_mpc(inp_file,
                 control_horizon,
                 control_time_step,
                 control_str_ids,
		 work_dir,
                 results_dir,
                 # target_depth_dict=target_depth_dict,
                 ngen=ngen,
                 nindividuals=nindividuals
                 )

if __name__ == "__main__":
    main()
```

Then to run it, you simply call the script with python:
```
python my_swmm_mpc.py
```
