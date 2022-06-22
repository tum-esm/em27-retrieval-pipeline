#!/bin/bash

init submodule proffaspylot
git submodule init

# download and unzip proffast v2.1.1
wget https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.1.1.zip
unzip PROFFASTv2.1.1.zip
rm PROFFASTv2.1.1.zip

# move proffast into correct subdirectory
rm -r src/pylot_1_1/prf
mv prf src/pylot_1_1/prf

# compile fortran code
cd src/pylot_1_1/prf
bash scripts/compile-proffast.sh
cd ../../..

# compile fortran code
cd src/detect_corrupt_ifgs
bash compile.sh

# install python dependencies
python3.9 -m venv .venv
source .venv/bin/activate
poetry install
