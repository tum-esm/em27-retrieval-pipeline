#!/bin/bash

# init submodule proffaspylot
git submodule init

# download and unzip proffast v2.0.1
wget https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.1.zip
unzip PROFFASTv2.1.zip
rm PROFFASTv2.1.zip

# move proffast into correct subdirectory
mv prf src/pylot/prf

compile proffast source code
cd src/pylot/prf

# bash install_proffast_linux.sh
# The install script includes invalid line endings, therefore I am just including it here
COMPILER="gfortran-8"
COMPILER_OPTIONS="-nocpp -O3 -o"
INSTALL_FOLDER=$(pwd)

str_win='character(len=1),parameter\s::\spathstr\s=\s"\\"'
str_lin='character(len=1),parameter::pathstr="/"'

echo "replace windows specific lines in source code ..."
for file in source/*/*90; do
	echo ${file}
	sed -i 's#'${str_win}'#'${str_lin}'#' $file
done

echo "compiling preprocess ..."
cd ${INSTALL_FOLDER}/source/preprocess/
${COMPILER} ${COMPILER_OPTIONS} ../../preprocess/preprocess4 glob_prepro4.F90 glob_OPUSparms.F90 preprocess4.F90

echo 'compiling inverse...'
cd ${INSTALL_FOLDER}/source/invers
${COMPILER} ${COMPILER_OPTIONS} ../../invers20 globinv20.f90 invers20.f90

echo 'compiling pcxs...'
cd ${INSTALL_FOLDER}/source/pcxs
${COMPILER} ${COMPILER_OPTIONS} ../../pcxs20 globvar20.f90 globlin20.f90 globlev20.f90 pcxs20.f90
echo 'done.'

cd ../../..

# install python dependencies
python3.9 -m venv .venv
source .venv/bin/activate
poetry install
