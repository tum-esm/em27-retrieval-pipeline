import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))

sys.path.append(f"{PROJECT_DIR}/src/pylot")
from prfpylot.pylot import Pylot

yaml_template_path = f"{PROJECT_DIR}/example/example-config-template.yml"
yaml_path = f"{PROJECT_DIR}/example/example-config.yml"
with open(yaml_template_path, "r") as f:
    yaml_content = "".join(f.readlines())
    yaml_content = yaml_content.replace("%PROJECT_DIR%", PROJECT_DIR)
with open(yaml_path, "w") as f:
    f.write(yaml_content)
Pylot(yaml_path, logginglevel="info").run(n_processes=1)

# TODO: Add tests for proffast 2.0.1 and 2.1.1
