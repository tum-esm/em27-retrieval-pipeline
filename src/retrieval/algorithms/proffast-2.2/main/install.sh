#!/bin/bash
# Compile the PROFFAST retrieval code for Linux.
#
# Requirements:  gfortran
# Creator:       Lena Feld, Friedrich Klappenbach
# Adapted by: 	 Moritz Makowski

set -o errexit

cd prf

INSTALL_FOLDER=$(pwd)
COMPILATION_FLAG=${1:-"-O3"}

echo "replacing windows specific line in source code ..."
for file in source/*/*90;
do
	echo "    $file"

	# mac os
	if [[ "$OSTYPE" == "darwin"* ]]; then
		LC_ALL=C sed -i "" "s|pathstr = \".*\"|pathstr = \"/\"|" "./$file"
		LC_ALL=C sed -i "" "s|character(150)|character(300)|" "./$file"
		LC_ALL=C sed -i "" "s|character(len=150)|character(300)|" "./$file"
		LC_ALL=C sed -i "" "s|character(200)|character(300)|" "./$file"
		LC_ALL=C sed -i "" "s|character(len=200)|character(len=300)|" "./$file"
	
	# linux
	else
		sed -i"" "s|pathstr = \".*\"|pathstr = \"/\"|" "./$file"
		sed -i"" "s|character(150)|character(300)|" "./$file"
		sed -i"" "s|character(len=150)|character(len=300)|" "./$file"
		sed -i"" "s|character(200)|character(300)|" "./$file"
		sed -i"" "s|character(len=200)|character(len=300)|" "./$file"
	fi
done

# Compile the source code
echo "compiling preprocess with flag $COMPILATION_FLAG ..."
cd "$INSTALL_FOLDER/source/preprocess/"
gfortran -nocpp $COMPILATION_FLAG -o ../../preprocess/preprocess4 glob_prepro4.F90 glob_OPUSparms.F90 preprocess4.F90

echo "compiling pcxs with flag $COMPILATION_FLAG ..."
cd "$INSTALL_FOLDER/source/pcxs"
gfortran -nocpp $COMPILATION_FLAG -o ../../pcxs20 globvar20.f90 globlin20.f90 globlev20.f90 pcxs20.f90

echo "compiling invers with flag $COMPILATION_FLAG ..."
cd "$INSTALL_FOLDER/source/invers"
gfortran -nocpp $COMPILATION_FLAG -o ../../invers20 globinv20.f90 invers20.f90

cd ..

echo '✨ done.'
