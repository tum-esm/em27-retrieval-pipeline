#!/bin/bash

# Stop on the first error
set -e errexit

# Check if the script is being run from the correct directory
if [ "$(pwd)" != "$(dirname $(realpath $0))" ]; then
    echo "Please run this script from the directory where it is located: $(dirname $(realpath $0))"
    exit 1
fi

# Preparation: Define directory where to find the config files
export ERP_CONFIG_DIR="$(dirname $(realpath $0))/config"

# Preparation: Clean up old results
rm -rf data/outputs/individual/proffast-2.4
rm -rf data/outputs/geoms/*.h5
rm -rf data/outputs/bundles/*.csv
rm -rf data/outputs/bundles/*.parquet
rm -rf data/outputs/reports/*.csv

# 1. Run the retrieval
echo "Running retrieval"
python ../cli.py retrieval run

# 2. Run the GEOMS export
python ../cli.py geoms run
cp data/outputs/individual/*/*/*/successful/*/groundbased_ftir.*.h5 data/outputs/geoms

# 3. Run the bundle export
python ../cli.py bundle run

# 4. Data report
python ../cli.py data-report
cp ../data/reports/mc.csv ../data/reports/so.csv data/outputs/reports
