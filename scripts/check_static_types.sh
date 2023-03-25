#!/bin/bash

set -o errexit

echo "Removing old mypy cache"
rm -rf .mypy_cache 

echo "Running checks on src/"
python -m mypy src/

echo "Running checks on tests/"
python -m mypy tests/
