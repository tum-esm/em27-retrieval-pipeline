import os
import filelock
from src import main

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE = f"{PROJECT_DIR}/src/main.lock"
lock = filelock.FileLock(LOCK_FILE, timeout=0)

"""
This script uses a file "src/main.lock" to save the information, whether the
automation is already running. If the automation is definitely not running but
you keep getting the "process is already running" message, you can just delete
that lock file and try again.
"""

if __name__ == "__main__":
    try:
        lock.acquire()
        try:
            main.run()
        finally:
            lock.release()
    except filelock.Timeout:
        print("process is already running")
