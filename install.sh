#!/bin/bash

# init submodule proffaspylot
git submodule init

# download and unzip proffast v2.0.1
wget https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.0.1.zip
unzip PROFFASTv2.0.1.zip
rm PROFFASTv2.0.1.zip

# compile source code
cd PROFFASTv2.0.1
bash install_proffast_linux.sh

# move into prfpylot
cd ..
mv PROFFASTv2.0.1 proffastpylot/prf

# install python dependencies
python3.9 -m venv .venv
source .venv/bin/activate
poetry install