import sys
import tum_esm_utils
import ftplib

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../.."))
from src import types, profiles


def run() -> None:
    config = types.Config.load()
    assert config.profiles is not None, "No profiles config found"

    try:
        for version in config.profiles.scope.models:
            print(f"Downloading {version} data")

            # Generate daily sensor sets
            missing_queries = profiles.generate_queries.generate_download_queries(
                config, version
            )
            if len(missing_queries) == 0:
                print("No data to request.")
                continue

            print("Connecting to FTP server")
            with ftplib.FTP(
                host="ccycle.gps.caltech.edu",
                passwd=config.profiles.server.email,
                user="anonymous",
                timeout=60,
            ) as ftp:
                print(f"Trying to download {len(missing_queries)} queries")
                fulfilled_queries = profiles.download_logic.download_data(
                    config, missing_queries, ftp, version
                )
                missing_queries = list(
                    set(missing_queries).difference(set(fulfilled_queries))
                )
                print(
                    f"Successfully downloaded {len(fulfilled_queries)} queries"
                )
                #profiles.upload_logic.upload_requests(
                #    config, missing_queries, ftp, version
                #)
                print(
                    "Done. Run this script again (after waiting " +
                    "a bit to download the reqested data)."
                )
    except KeyboardInterrupt:
        print("Interrupted by user.")
        exit(1)


if __name__ == "__main__":
    run()
