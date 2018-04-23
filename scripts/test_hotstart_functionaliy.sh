#!/bin/bash
build_swmm.sh
hsdir=../simple_model/hotstart_test/
cd $hsdir

#run and plot the model with no hotstart
swmm5 no_hs.inp no_hs.rpt

#create a hotstart file with the original program ending partly through the simulation
wrt_model=write_hs_orig.inp
prfx=write_hs_swmm
swmm_model=$prfx.inp
swmm_model_rpt=$prfx.rpt
cp  $wrt_model $swmm_model 
sed -i -e 's/<hsfile>/swmm/g' $swmm_model
swmm5 $swmm_model $swmm_model_rpt

#create a hotstart file with the modified program ending partly through the simulation
prfx=write_hs_mod
mod_model=$prfx.inp
mod_model_rpt=$prfx.rpt
cp  $wrt_model $mod_model 
sed -i -e 's/<hsfile>/mod/g' $mod_model
run-swmm $mod_model $mod_model_rpt

##create a hotstart file pyswmm at same moment 
prfx=write_hs_pyswmm
mod_model=$prfx.inp
mod_model_rpt=$prfx.rpt
cp  no_hs.inp $mod_model 
python ../../scripts/pyswmm_make_hotstart.py $mod_model


#run read model with all three hotstart files
read_model=read_hs.inp
cp read_hs_orig.inp $read_model
sed -i -e 's/<hsfile>/mod/g' $read_model
swmm5 $read_model mod_hs.rpt

cp read_hs_orig.inp $read_model
sed -i -e 's/<hsfile>/swmm/g' $read_model
swmm5 $read_model swmm_hs.rpt

cp read_hs_orig.inp $read_model
sed -i -e 's/<hsfile>/pyswmm/g' $read_model
swmm5 $read_model pyswmm_hs.rpt

#plot the model results
python ../../scripts/plot_rpt.py swmm_hs.rpt "NODE J1" Depth
python ../../scripts/plot_rpt.py pyswmm_hs.rpt "NODE J1" Depth
python ../../scripts/plot_rpt.py mod_hs.rpt "NODE J1" Depth
