#!/bin/bash
# Compile the PROFFAST retrieval code for Linux.
#
# Requirements:  gfortran
# Creator:       Lena Feld, Friedrich Klappenbach
# Adapted by: 	 Moritz Makowski

set -o errexit

cd prf

INSTALL_FOLDER=$(pwd)

echo "replacing windows specific line in source code ..."
for file in source/*/*90;
do
	echo "    $file"

	# mac os
	if [[ "$OSTYPE" == "darwin"* ]]; then
		LC_ALL=C sed -i "" "s|pathstr = \".*\"|pathstr = \"/\"|" "./$file"
		LC_ALL=C sed -i "" "s|character(200)|character(300)|" "./$file"
		LC_ALL=C sed -i "" "s|character(len=200)|character(len=300)|" "./$file"
	
	# linux
	else
		sed -i"" "s|pathstr = \".*\"|pathstr = \"/\"|" "./$file"
		sed -i"" "s|character(200)|character(300)|" "./$file"
		sed -i"" "s|character(len=200)|character(len=300)|" "./$file"
	fi
done

# Compile the source code
echo "compiling preprocess ..."
cd "$INSTALL_FOLDER/source/preprocess/"
gfortran -nocpp -O3 -o ../../preprocess/preprocess6 glob_prepro6.F90 glob_OPUSparms6.F90 preprocess6.F90

echo 'compiling pcxs ...'
cd "$INSTALL_FOLDER/source/pcxs"
gfortran -nocpp -O3 -o ../../pcxs24 globvar24.f90 globlin24.f90 globlev24.f90 pcxs24.f90

echo 'compiling invers ...'
cd "$INSTALL_FOLDER/source/invers"
gfortran -nocpp -O3 -o ../../invers25 globinv25.f90 invers25.f90

cd ..

echo '✨ done.'
