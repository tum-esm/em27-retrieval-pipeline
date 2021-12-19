import json
import os
from src import (
    update_automation_report,
    validate_configuration,
)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(f"{PROJECT_DIR}/config.json") as f:
    config = json.load(f)
    validate_configuration.run()


if __name__ == "__main__":
    dates = update_automation_report.run()
    print(dates)
