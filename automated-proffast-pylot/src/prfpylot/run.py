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
    assert len(sys.argv) == 3, (
        "wrong number of arguments provided to run.py. Example"
        + ' call: "./run.py container_id pylot_config_path"'
    )

    container_id, pylot_config_path = sys.argv[1:]
    container_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "containers",
        f"pylot-container-{container_id}",
    )
    assert os.path.isdir(container_path), "container does not exist"

    print(
        f'executing in container_id "{container_id}" '
        + f'at container_path "{container_path}" and '
        + f'pylot_config_path "{pylot_config_path}".'
    )
    sys.path.append(container_path)
    pylot = importlib.import_module("prfpylot.pylot")
    pylot.Pylot(pylot_config_path, logginglevel="info").run(n_processes=1)
