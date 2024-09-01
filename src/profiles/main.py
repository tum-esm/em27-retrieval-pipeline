import os
import sys
import tum_esm_utils
import ftplib

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../.."))
from src import types, profiles


def run() -> None:
    config = types.Config.load()
    assert config.profiles is not None, "No profiles config found"

    for variant in ["GGG2014", "GGG2020"]:
        os.makedirs(
            os.path.join(
                config.general.data.atmospheric_profiles.root, variant
            ),
            exist_ok=True
        )

    try:
        if len(config.profiles.GGG2020_standard_sites) > 0:
            print("Downloading standard site data")
            with ftplib.FTP(
                host="ccycle.gps.caltech.edu",
                passwd=config.profiles.server.email,
                user="anonymous",
                timeout=60,
            ) as ftp:
                print("Connected to FTP server")
                profiles.std_site_logic.download_data(config, ftp)
        else:
            print("No standard site data to download")

        if config.profiles.scope is None:
            print("No scope defined, skipping on-demand data download")
            return

        for profile_model in config.profiles.scope.models:
            print(f"Downloading on-demand {profile_model} data")

            with ftplib.FTP(
                host="ccycle.gps.caltech.edu",
                passwd=config.profiles.server.email,
                user="anonymous",
                timeout=60,
            ) as ftp:
                print("Connected to FTP server")
                cache = profiles.cache.DownloadQueryCache.load()
                running_queries = cache.get_active_queries(profile_model)
                print(f"Found {len(running_queries)} already requested queries")
                still_running_query_count = len(running_queries)
                if len(running_queries) > 0:
                    print(f"Trying to download {len(running_queries)} queries")
                    fulfilled_queries = profiles.download_logic.download_data(
                        config, running_queries, ftp, profile_model
                    )
                    print(
                        f"Successfully downloaded {len(fulfilled_queries)} queries"
                    )
                    cache.remove_queries(profile_model, fulfilled_queries)

                    cache.dump()
                    print("Updated cache")

                    still_running_query_count = len(
                        cache.get_timed_out_queries(profile_model)
                    )

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
                outstanding_download_queries = profiles.generate_queries.generate_download_queries(
                    config, profile_model
                )

                if len(outstanding_download_queries) == 0:
                    print("No data to request.")
                    continue

                # queries might not be in cache anymore but still
                # downloadable from the server
                print(
                    f"Trying to download {len(outstanding_download_queries)} queries"
                )
                fulfilled_queries = profiles.download_logic.download_data(
                    config, outstanding_download_queries, ftp, profile_model
                )
                outstanding_download_queries = sorted(
                    set(outstanding_download_queries).difference(
                        set(fulfilled_queries)
                    ),
                    key=lambda q: q.from_date,
                    reverse=True,
                )
                print(
                    f"Successfully downloaded {len(fulfilled_queries)} queries"
                )
                new_download_queries = sorted(
                    list(
                        set(outstanding_download_queries) -
                        set(fulfilled_queries) -
                        set(cache.get_active_queries(profile_model))
                    ),
                    key=lambda q: q.from_date,
                    reverse=True,
                )

                query_count = min(open_query_count, len(new_download_queries))
                print(
                    f"Requesting {query_count} out of {len(new_download_queries)} queries"
                )
                profiles.upload_logic.upload_requests(
                    config, new_download_queries[: query_count], ftp,
                    profile_model
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
