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

                profiles.std_site_logic.download_data(config, ftp)

                cache = profiles.cache.DownloadQueryCache.load()
                running_queries = cache.get_active_queries(version)
                print(f"Found {len(running_queries)} already requested queries")
                still_running_query_count = len(running_queries)
                if len(running_queries) > 0:
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
                    still_running_query_count = len(running_queries
                                                   ) - len(fulfilled_queries)

                open_query_count = config.profiles.server.max_parallel_requests - still_running_query_count

                print(f"{still_running_query_count} queries are still running")
                if open_query_count <= 0:
                    print(
                        "No open slots for new queries " +
                        "(config.profiles.server.max_parallel_requests = " +
                        f"{config.profiles.server.max_parallel_requests})"
                    )
                    continue
                else:
                    print(f"{open_query_count} open slots for new queries")

                # Generate daily sensor sets
                missing_queries = profiles.generate_queries.generate_download_queries(
                    config, version
                )
                if len(missing_queries) == 0:
                    print("No data to request.")
                    continue

                # queries might not be in cache anymore but still
                # downloadable from the server
                print(f"Trying to download {len(missing_queries)} queries")
                fulfilled_queries = profiles.download_logic.download_data(
                    config, missing_queries, ftp, version
                )
                missing_queries = sorted(
                    set(missing_queries).difference(set(fulfilled_queries)),
                    key=lambda q: q.from_date,
                    reverse=True,
                )
                print(
                    f"Successfully downloaded {len(fulfilled_queries)} queries"
                )
                query_count = min(open_query_count, len(missing_queries))
                print(
                    f"Requesting {query_count} out of {len(missing_queries)} queries"
                )
                profiles.upload_logic.upload_requests(
                    config, missing_queries[: query_count], ftp, version
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
