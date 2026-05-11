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
echo "Retrieval completed successfully."

# 2. Run the GEOMS export

python ../cli.py geoms run

# 3. Run the bundle export

# TODO
