import os
import sys

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

# Required by imports within the proffastpylot
sys.path.insert(0, f"{PROJECT_DIR}/proffastpylot")

from proffastpylot.prfpylot.pylot import Pylot

def run(site: str, date: str):
    Pylot(f"{PROJECT_DIR}/inputs/{site}_{date}.yml", logginglevel="info").run()
