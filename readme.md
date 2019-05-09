# swmm_mpc 
`swmm_mpc` is a python package that can be used to perform model predictive control (MPC) for EPASWMM5 ([Environmental Protection Agency Stormwater Management Model](https://www.epa.gov/water-research/storm-water-management-model-swmm)). `swmm_mpc` relies on the [pyswmm package](https://github.com/OpenWaterAnalytics/pyswmm) which enables the step by step running of SWMM5 models through Python.

`swmm_mpc` has only been tested **Python 2.7** on **Ubuntu 16.10** and **RedHat**. The modified version of OWASWMM5 included in the `pyswmm` library was compiled on Ubuntu 16.10 and will therefore will not work in a Windows environment.

# Installation
## 1. Install swmm_mpc
```
git clone https://github.com/UVAdMIST/swmm_mpc.git
pip install swmm_mpc/
```
## 2. Install pyswmm
swmm\_mpc requires a special version of OWA's pyswmm. This version of pyswmm has an additional feature that allows saving a hotstart file at any time step in the simulation run. To install this version of pyswmm do:

```
pip install git+https://github.com/UVAdMIST/pyswmm.git@feature_save_hotstart
```

## 3. Install EPASWMM5 
You will also need to have a working version of EPASWMM5 on your machine and have it added to the path. You can download the source code from the [EPA Website](https://www.epa.gov/water-research/storm-water-management-model-swmm). In Linux you can do this as follows:
```
wget https://www.epa.gov/sites/production/files/2017-03/swmm51012_engine_2.zip
unzip swmm51012_engine_2.zip -d swmm5
cd swmm5/
unzip source5_1_012.zip -d src
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
you will likely use. Here is an example of how it is used. `run_swmm_mpc` takes one and only one argument: the path to your configuration file (see example below).   First I write a small 
script to indicate the model and the different parameters I want to use, like 
this (called `my_swmm_mpc.py` in the next step):


## configuration file
The configuration file is a json file that specifies all of the parameters you will be using in your swmm_mpc run. There are certain parameters that are required to be specified and others that have a default value and are not required.

### Required parameters in configuration file
1. `inp_file_path`: [string] path to .inp file relative to config file
2. `ctl_horizon`: [number] ctl horizon in hours
3. `ctl_time_step`: [number] control time step in seconds
4. `ctl_str_ids`: [list of strings] ids of control structures for which controls policies will be found. Each should start with one of the key words ORIFICE, PUMP, or WEIR e.g., [ORIFICE R1, ORIFICE R2]
5. `work_dir`: [string] directory relative to config file where the temporary files will be created
6. `results_dir`: [string] directory relative to config file where the results will be written
7. `opt_method`: [string] optimization method. Currently supported methods are 'genetic_algorithm', and 'bayesian_opt'
8. `optimization_params`: [dict] dictionary with key values that will be passed to the optimization function for GA this includes
    * `ngen`: [int] number of generations for GA
    * `nindividuals`: [int] number of individuals for initial generation in GA
9. `run_suffix`: [string] will be added to the results filename

### Optional parameters in configuration file
1. `flood_weight`: [number] overall weight for the sum of all flooding relative to the overall weight for the sum of the absolute deviations from target depths (`dev_weight`). Default: 1
2. `dev_weight`: [number] overall weight for the sum of the absolute deviations from target depths. This weight is relative to the `flood_weight` Default: 0
3. `target_depth_dict`: [dict] dictionary where the keys are the nodeids and the values are a dictionary. The inner dictionary has two keys, 'target', and 'weight'. These values specify the target depth for the nodeid and the weight given to that in the cost function.  e.g., {'St1': {'target': 1, 'weight': 0.1}} Default: None (flooding from all nodes is weighted equally)
4. `node_flood_weight_dict`: [dict] dictionary where the keys are the node ids and the values are the relative weights for weighting the amount of flooding for a given node. e.g., {'st1': 10, 'J3': 1}. Default: None

## Example 
### Example configuration file
 
```
{
    "inp_file_path": "my_swmm_model.inp",
    "ctl_horizon": 1,
    "ctl_time_step": 900,
    "ctl_str_ids": ["ORIFICE R1", "ORIFICE R2"],
    "work_dir": "work/",
    "results_dir": "results/",
    "dev_weight":0.5,
    "flood_weight":1000,
    "run_suffix": "my_mpc_run",
    "opt_method": "genetic_algorithm",
    "optimization_params":
        {
                    "num_cores":20,
                    "ngen":8,
                    "nindividuals":120
                },
    "target_depth_dict":
        {
            "Node St1":
                {
                    "target":1.69,
                    "weight":1
                },
            "Node St2":
                {
                    "target":1.69,
                    "weight":1
                }
        }
} 
```
### Example python file
```python

from swmm_mpc.swmm_mpc import run_swmm_mpc
run_swmm_mpc('my_config_file.json')
```

Then to run it, you simply call the script with python:
```
python my_swmm_mpc.py
```
# Dockerized code
A Docker image with swmm_mpc and all of its dependencies can be found at [https://hub.docker.com/r/jsadler2/swmm_mpc/](https://hub.docker.com/r/jsadler2/swmm_mpc/). You would run it like so (**this assumes your results\_dir, your workdir, your .inp file, and your config file (\*.json) are all in the same directory): 

```
docker run -v /path/to/run_dir/:/run_dir/ jsadler2/swmm_mpc:latest python /run_script.py
```
# Example model 
An example use case model is found on HydroShare: [https://www.hydroshare.org/resource/73b38d6417ac4352b9dae38a78a47d81/](https://www.hydroshare.org/resource/73b38d6417ac4352b9dae38a78a47d81/).
