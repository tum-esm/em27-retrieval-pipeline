#!/bin/bash

# The original install script includes invalid line endings,
# therefore I am just including it here. This script has to 
# be run inside the src/pylot_x_x/prf directory

COMPILER="gfortran-9"
COMPILER_OPTIONS="-nocpp -O3 -o"
INSTALL_FOLDER=$(pwd)
STR_WIN='character(len=1),parameter\s::\spathstr\s=\s"\\"'
STR_LIN='character(len=1),parameter::pathstr="/"'

echo "replace windows specific lines in source code ..."
for file in source/*/*90; do
	echo ${file}
	sed -i 's#'${STR_WIN}'#'${STR_LIN}'#' $file
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