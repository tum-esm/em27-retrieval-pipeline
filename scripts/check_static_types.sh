#!/bin/bash

set -o errexit

echo "Removing old mypy cache"
rm -rf .mypy_cache 

echo "Running checks on src/run_automated_proffast.py"
python -m mypy src/run_automated_proffast.py

# TODO: tests
