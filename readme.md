# swmm_mpc 
`swmm_mpc` is a python package that can be used to perform model predictive control (MPC) for EPASWMM5 ([Environmental Protection Agency Stormwater Management Model](https://www.epa.gov/water-research/storm-water-management-model-swmm)). `swmm_mpc` relies on the [pyswmm package](https://github.com/OpenWaterAnalytics/pyswmm) which enables the step by step running of SWMM5 models through Python.  

# Installation
```
git clone https://github.com/uva-hydroinformatics/swmm_mpc.git
pip install swmm_mpc/
```
swmm\_mpc requires a special version of OWA's pyswmm. To install this do:

```
pip install git+git://github.com/uva-hydroinformatics/pyswmm.git@feature_save_hotstart
```

You will also need to have a working version of EPASWMM5 on your machine and have it added to the path.

