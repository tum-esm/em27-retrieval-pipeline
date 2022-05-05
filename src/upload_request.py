import os
import subprocess
import tenacity
from src import utils, load_config

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
CONFIG = load_config.run()

class ServerError553(Exception):
    pass

@tenacity.retry(
    retry=tenacity.retry_if_exception_type(ServerError553),
    stop=tenacity.stop_after_attempt(2),
    wait=tenacity.wait_fixed(60)
)
def _upload():
    result = subprocess.run(
        ["bash", f"{PROJECT_DIR}/upload_request.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ.copy(), "PASSWD": CONFIG["user"]},
    )
    if "Access failed: 553" in result.stderr.decode():
        raise ServerError553
    elif result.returncode != 0:
        raise Exception(result.stderr.decode())


def run(start_date: str, end_date: str):
    with open(f"input_file.txt", "w") as f:
        f.write(
            "\n".join(
                [
                    CONFIG["stationId"],
                    start_date,
                    end_date,
                    str(round(CONFIG["lat"])),
                    str(round(CONFIG["lng"])),
                    CONFIG["user"],
                ]
            )
        )
    
    try:
        _upload()
    except Exception as e:
        utils.print_red(f"Request-uploading failed: {e}")
