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

            with ftplib.FTP(
                host="ccycle.gps.caltech.edu",
                passwd=config.profiles.server.email,
                user="anonymous",
                timeout=60,
            ) as ftp:
                print("Connected to FTP server")

                cache = profiles.cache.DownloadQueryCache.load()
                running_queries = cache.get_active_queries(version)
                print(f"Found {len(running_queries)} already requested queries")
                print(f"Trying to download {len(running_queries)} queries")
                fulfilled_queries = profiles.download_logic.download_data(
                    config, running_queries, ftp, version
                )
                print(
                    f"Successfully downloaded {len(fulfilled_queries)} queries"
                )
                cache.remove_queries(version, fulfilled_queries)
                cache.dump()
                print("Updated cache")

                # Generate daily sensor sets
                missing_queries = profiles.generate_queries.generate_download_queries(
                    config, version
                )
                if len(missing_queries) == 0:
                    print("No data to request.")
                    continue

                print(f"Trying to download {len(missing_queries)} queries")
                fulfilled_queries = profiles.download_logic.download_data(
                    config, missing_queries, ftp, version
                )
                missing_queries = sorted(
                    set(missing_queries).difference(set(fulfilled_queries)),
                    key=lambda q: q.from_date,
                )
                print(
                    f"Successfully downloaded {len(fulfilled_queries)} queries"
                )
                print(f"Requesting {len(missing_queries)} queries")
                profiles.upload_logic.upload_requests(
                    config, missing_queries, ftp, version
                )
                print(
                    "Done. Run this script again (after waiting " +
                    "a bit to download the reqested data)."
                )
    except KeyboardInterrupt:
        print("Interrupted by user.")
        exit(1)


if __name__ == "__main__":
    run()
