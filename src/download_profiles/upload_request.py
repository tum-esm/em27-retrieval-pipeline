import os
import subprocess
import tenacity
from src import download_profiles

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

class ServerError553(Exception):
    pass

@tenacity.retry(
    retry=tenacity.retry_if_exception_type(ServerError553),
    stop=tenacity.stop_after_attempt(2),
    wait=tenacity.wait_fixed(60)
)
def _upload(config: dict):
    result = subprocess.run(
        ["bash", f"{PROJECT_DIR}/src/download_profiles/upload_request.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ.copy(), "PASSWD": config["user"]},
        timeout=60,
    )
    if "Access failed: 553" in result.stderr.decode():
        raise ServerError553
    elif result.returncode != 0:
        raise Exception(result.stderr.decode())


def run(start_date: str, end_date: str, config: dict):
    with open(f"input_file.txt", "w") as f:
        f.write(
            "\n".join(
                [
                    config["stationId"],
                    start_date,
                    end_date,
                    str(round(config["lat"])),
                    str(round(config["lon"])),
                    config["user"],
                ]
            )
        )
    
    try:
        _upload(config)
    except Exception as e:
        download_profiles.utils.print_red(f"Request-uploading failed: {e}")
