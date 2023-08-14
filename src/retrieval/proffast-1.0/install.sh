#!/bin/bash
# Compile the PROFFAST retrieval code for Linux.
#
# Requirements:  gfortran
# Creator:       Lena Feld, Friedrich Klappenbach
# Adapted by: 	 Moritz Makowski

set -o errexit

cd prf

INSTALL_FOLDER=$(pwd)

# Compile the source code
echo "compiling preprocess ..."
cd "$INSTALL_FOLDER/source/2020-06-12_sources-preprocess_Linux"
gfortran -nocpp -O3 -o ../../preprocess/preprocess4 glob_prepro4.F90 glob_OPUSparms.F90 preprocess4.F90

echo 'compiling pcxs ...'
cd "$INSTALL_FOLDER/source/2020-07-15_sources-pcxs10_Linux"
gfortran -nocpp -O3 -o ../../pcxs10 globvar10.f90 globlin10.f90 globlev10.f90 pcxs10.f90

echo 'compiling invers ...'
cd "$INSTALL_FOLDER/source/2021-02-05_sources-invers10_Linux"
gfortran -nocpp -O3 -o ../../invers10 globinv10.f90 invers10.f90

cd ..

echo '✨ done.'
