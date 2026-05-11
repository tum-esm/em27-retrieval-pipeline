#!/bin/bash

set -e errexit
export ERP_CONFIG_DIR="$(dirname $(realpath $0))/config"

# i.e. cd .../example && bash run.sh
if [ "$(pwd)" != "$(dirname $(realpath $0))" ]; then
    echo "Please run this script from the directory where it is located: $(dirname $(realpath $0))"
    exit 1
fi

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