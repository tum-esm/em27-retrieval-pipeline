import filelock
from src.utils import load_setup
from src import main

PROJECT_DIR, CONFIG = load_setup()
lock_path = f"{PROJECT_DIR}/main.lock"
lock = filelock.FileLock(lock_path, timeout=0)


if __name__ == "__main__":
    try:
        lock.acquire()
        try:
            main.run()
        finally:
            lock.release()
    except filelock.Timeout:
        # If you know what you are doing, you can remove the "main.lock" file
        print("process is already running")
