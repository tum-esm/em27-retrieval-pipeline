#!/bin/bash
# Compile the PROFFAST retrieval code for Linux.
#
# Requirements:  gfortran
# Creator:       Lena Feld, Friedrich Klappenbach
# Adapted by: 	 Moritz Makowski

set -o errexit

echo "replacing windows specific line in source code ..."
for file in source/*/*90;
do
	echo "    $file"

	# mac os
	if [[ "$OSTYPE" == "darwin"* ]]; then
		LC_ALL=C sed -i "" "s|pathstr = \".*\"|pathstr = \"/\"|" "./$file"
	
	# linux
	else
		sed -i"" "s|pathstr = \".*\"|pathstr = \"/\"|" "./$file"
	fi
done

cd prf

INSTALL_FOLDER=$(pwd)

# Compile the source code
echo "compiling preprocess ..."
cd "$INSTALL_FOLDER/../source/preprocess4"
gfortran -nocpp -O3 -o $INSTALL_FOLDER/preprocess/preprocess4 glob_prepro4.F90 glob_OPUSparms.F90 preprocess4.F90

echo 'compiling pcxs ...'
cd "$INSTALL_FOLDER/../source/pcxs10"
gfortran -nocpp -O3 -o $INSTALL_FOLDER/pcxs10 globvar10.f90 globlin10.f90 globlev10.f90 pcxs10.f90

echo 'compiling invers ...'
cd "$INSTALL_FOLDER/../source/invers10"
gfortran -nocpp -O3 -o $INSTALL_FOLDER/invers10 globinv10.f90 invers10.f90

cd ..

echo '✨ done.'
