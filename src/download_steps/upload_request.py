import os
import subprocess
import tenacity
from src.utils import load_setup

PROJECT_DIR, CONFIG = load_setup(validate=False)


class ServerError553(Exception):
    pass

@tenacity.retry(
    retry=tenacity.retry_if_exception_type(ServerError553),
    stop=tenacity.stop_after_attempt(2),
    wait=tenacity.wait_fixed(60)
)
def _upload():
    result = subprocess.run(
        ["bash", f"{PROJECT_DIR}/src/download_steps/upload_request.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ.copy(), "PASSWD": CONFIG["user"]},
        timeout=60,
    )
    if "Access failed: 553" in result.stderr.decode():
        raise ServerError553
    elif result.returncode != 0:
        raise Exception(result.stderr.decode())


def run(query):
    with open(f"input_file.txt", "w") as f:
        f.write(
            "\n".join(
                [
                    query.sensor,
                    query.t_from_str,
                    query.t_to_str,
                    str(round(query.lat)),
                    str(round(query.lon)),
                    CONFIG["user"],
                ]
            )
        )
    
    try:
        _upload()
    except Exception as e:
        print(f"Request-uploading failed: {e}")
