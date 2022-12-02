#!/bin/python
"""
Script to run a particular Pylot instance

example:

./run.py container_id config_path
"""
import sys
import os
import importlib

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("Wrong number of arguments provided to run.py")
        sys.stderr.write("example: ./run.py container_id config_path")
        sys.exit(2)

    container_id = sys.argv[1]
    config_path = sys.argv[2]
    print(f"executing in container_id: {container_id}")
    container_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), container_id)
    if os.path.exists(container_path) != True:
        sys.stderr.write("Container does not exist.")
        sys.exit(1)
    
    sys.path.append(container_path)
    pylot = importlib.import_module('prfpylot.pylot')
    pylot.Pylot(config_path, logginglevel="info").run(n_processes=1)