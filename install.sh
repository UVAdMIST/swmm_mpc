if ! [ -x "$(command -v unzip)" ]; then
	sudo apt install unzip
fi

source activate swmm-mpc-py

#git clone https://github.com/UVAdMIST/swmm_mpc.git
pip install .

pip install git+git://github.com/uva-hydroinformatics/pyswmm.git@feature_save_hotstart

cd ~
wget https://www.epa.gov/sites/production/files/2017-03/swmm51012_engine_2.zip
unzip swmm51012_engine_2.zip -d swmm5
cd swmm5/
unzip source5_1_012.zip -d src
unzip makefiles.zip -d mk
cd mk
unzip GNU-CLE.zip -d gnu
cp gnu/Makefile ../src/
cd ../src

sed -i -e 's/#define DLL/\/\/#define DLL/g' swmm5.c
sed -i -e 's/\/\/#define CLE/#define CLE/g' swmm5.c

if ! [ -x "$(command -v make)" ]; then
	sudo apt install build-essential
fi

make

export PATH="~/swmm5/src:$PATH"
echo 'PATH="~/swmm5/src:$PATH"' >> ~/.bashrc
