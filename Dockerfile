FROM python:2.7-slim-stretch

RUN apt update
RUN apt install -y git gcc make wget unzip tk
RUN pip install numpy
RUN pip install git+https://github.com/UVAdMIST/swmm_mpc


RUN wget https://www.epa.gov/sites/production/files/2017-03/swmm51012_engine_2.zip
RUN mkdir swmm5
RUN unzip swmm51012_engine_2.zip -d swmm5
WORKDIR swmm5/
RUN mkdir src
RUN unzip source5_1_012.zip -d src
RUN mkdir mk
RUN unzip makefiles.zip -d mk
WORKDIR mk/
RUN mkdir gnu
RUN unzip GNU-CLE.zip -d gnu
RUN cp gnu/Makefile ../src/
WORKDIR ../src

RUN sed -i -e 's/#define DLL/\/\/#define DLL/g' swmm5.c
RUN sed -i -e 's/\/\/#define CLE/#define CLE/g' swmm5.c
RUN make 
ENV PATH="/swmm5/src:${PATH}"
WORKDIR /
