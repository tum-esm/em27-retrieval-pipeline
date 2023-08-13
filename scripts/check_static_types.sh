#!/bin/bash

set -o errexit

echo "Removing old mypy cache"
rm -rf .mypy_cache 

for file in "src/run_automated_proffast.py" "src/download_atmospheric_profiles.py" "tests/" "src/export_retrieval_outputs.py"
do
    echo "Running checks on $file"
    python -m mypy $file
done

# TODO: move to tests
# TODO: add scripts directory
# TODO: add cli directory
