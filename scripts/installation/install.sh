#!/bin/bash

# init submodule proffaspylot
git submodule init

# download and unzip proffast v2.0.1
wget https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.2.zip
unzip PROFFASTv2.2.zip
rm PROFFASTv2.2.zip

# move proffast into correct subdirectory
if [[ -d src/prfpylot/prf ]]
then
    rm -r src/prfpylot/prf
fi
mv prf src/prfpylot

# compile fortran code
cd src/prfpylot/prf
bash install_proffast_linux.sh 
cd ../../..

# compile fortran code
cd src/detect_corrupt_ifgs
bash compile.sh
cd ../..

# install python dependencies
python3.9 -m venv .venv
source .venv/bin/activate
poetry install
