#!/bin/bash
# Compile the PROFFAST retrieval code for Linux.
#
# Requirements:  gfortran
# Creator:       Lena Feld, Friedrich Klappenbach
# Adapted by: 	Moritz Makowski

set -o errexit

INSTALL_FOLDER=$(pwd)

# Compile the source code
echo "compiling preprocess ..."
cd "$INSTALL_FOLDER/source/preprocess/"
gfortran -nocpp -O3 -o ../../preprocess/preprocess4 glob_prepro4.F90 glob_OPUSparms.F90 preprocess4.F90

echo 'compiling pcxs ...'
cd "$INSTALL_FOLDER/source/pcxs"
gfortran -nocpp -O3 -o ../../pcxs20 globvar20.f90 globlin20.f90 globlev20.f90 pcxs20.f90

echo 'compiling invers ...'
cd "$INSTALL_FOLDER/source/invers"
gfortran -nocpp -O3 -o ../../invers20 globinv20.f90 invers20.f90

echo '✨ done.'
