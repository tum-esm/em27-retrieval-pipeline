#!/bin/bash

set -o errexit

echo "Removing old mypy cache"
rm -rf .mypy_cache 

for file in "src/run_automated_proffast.py" "src/download_vertical_profiles.py"
do
    echo "Running checks on $file"
    python -m mypy $file
done

# TODO: tests
