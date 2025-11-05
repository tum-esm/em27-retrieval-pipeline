import datetime
import os
import re
import sys
from typing import Optional

import em27_metadata
import polars as pl
import tqdm
import tum_esm_utils

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../.."))
from src import types, utils

from .load_results import load_results_directory


def run(
    config: Optional[types.Config] = None,
    em27_metadata_interface: Optional[em27_metadata.interfaces.EM27MetadataInterface] = None,
) -> None:
    if config is None:
        print("Loading configuration")
        config = types.Config.load()

    assert config.bundles is not None, "no bundle targets found"
    assert len(config.bundles) > 0, "no bundle targets found"

    if em27_metadata_interface is None:
        em27_metadata_interface = utils.metadata.load_local_em27_metadata_interface()
        if em27_metadata_interface is not None:
            print("Found local metadata")
        else:
            print("Did not find local metadata -> fetching metadata from GitHub")
            assert config.general.metadata is not None, "Remote metadata not configured"
            em27_metadata_interface = em27_metadata.load_from_github(
                github_repository=config.general.metadata.github_repository,
                access_token=config.general.metadata.access_token,
            )
            print("Successfully fetched metadata from GitHub")

    for i, bundle_target in enumerate(config.bundles):
        print(f"Processing bundle target #{i + 1}")
        print(f"Bundle target: {bundle_target.model_dump_json(indent=4)}")

        for retrieval_algorithm in bundle_target.retrieval_algorithms:
            for atmospheric_profile_model in bundle_target.atmospheric_profile_models:
                if (retrieval_algorithm == "proffast-1.0") and (
                    atmospheric_profile_model == "GGG2020"
                ):
                    print("Skipping proffast-1.0/GGG2020 as it is not supported")
                    continue
                print(f"Processing {retrieval_algorithm}/{atmospheric_profile_model}")
                for sensor_id in bundle_target.sensor_ids:
                    dfs: list[pl.DataFrame] = []

                    d = os.path.join(
                        config.general.data.results.root,
                        retrieval_algorithm,
                        atmospheric_profile_model,
                        sensor_id,
                        "successful",
                    )
                    print(f"  Sensor {sensor_id}: looking for files in {d}")

                    # fmt: off
                    results_pattern =                re.compile(r"^\d{8}(_\d{6}_\d{6})?(_.+)?$")
                    results_pattern_without_suffix = re.compile(r"^\d{8}(_\d{6}_\d{6})?$")
                    results_pattern_with_suffix =    re.compile(r"^\d{8}(_\d{6}_\d{6})?(_.+)$")
                    # fmt: on

                    all_results = [
                        r
                        for r in os.listdir(d)
                        if os.path.isdir(os.path.join(d, r)) and results_pattern.match(r)
                    ]
                    print(f"    Found {len(all_results)} results directories")

                    if bundle_target.retrieval_job_output_suffix is None:
                        matching_results = [
                            r for r in all_results if results_pattern_without_suffix.match(r)
                        ]
                        print(
                            f"    Found {len(matching_results)} results directories with output suffix `None`"
                        )
                    else:
                        matching_results = [
                            r
                            for r in all_results
                            if results_pattern_with_suffix.match(r)
                            and r.endswith(bundle_target.retrieval_job_output_suffix)
                        ]
                        print(
                            f"    Found {len(matching_results)} results directories matching the output suffix"
                        )

                    timed_results: list[str] = sorted(
                        [
                            r
                            for r in matching_results
                            if (
                                (
                                    bundle_target.from_datetime.date()
                                    <= datetime.datetime.strptime(r[:8], "%Y%m%d").date()
                                )
                                and (
                                    datetime.datetime.strptime(r[:8], "%Y%m%d").date()
                                    <= bundle_target.to_datetime.date()
                                )
                            )
                        ]
                    )
                    print(
                        f"    Found {len(timed_results)} results directories matching the time range"
                    )

                    progress = tqdm.tqdm(timed_results, dynamic_ncols=True, desc="    ...")
                    for result in progress:
                        progress.desc = f"    {result}"
                        progress.refresh()
                        df = load_results_directory(
                            os.path.join(d, result),
                            sensor_id,
                            retrieval_algorithm,
                            parse_dc_timeseries=bundle_target.parse_dc_timeseries,
                            parse_retrieval_diagnostics=bundle_target.parse_retrieval_diagnostics,
                            retrieval_job_output_suffix=bundle_target.retrieval_job_output_suffix,
                        )
                        if df is not None:
                            dfs.append(df)

                    combined_df = pl.concat(dfs, how="diagonal").sort("utc")

                    # Attach a column "campaign_ids" to the data to make it
                    # easy to filter it by individual campaigns
                    matching_campaign_ids: list[str] = ["" for _ in range(len(combined_df))]
                    utcs = combined_df["utc"].to_list()
                    location_ids = combined_df["location_id"].to_list()
                    for c in em27_metadata_interface.campaigns.root:
                        if sensor_id not in c.sensor_ids:
                            continue
                        for i in range(len(combined_df)):
                            if (location_ids[i] in c.location_ids) and (
                                c.from_datetime <= utcs[i] <= c.to_datetime
                            ):
                                matching_campaign_ids[i] += f"+{c.campaign_id}"
                    matching_campaign_ids = [s.lstrip("+") for s in matching_campaign_ids]
                    combined_df = combined_df.with_columns(
                        pl.Series("campaign_ids", matching_campaign_ids)
                    )

                    name = f"em27-retrieval-bundle-{sensor_id}-{retrieval_algorithm}-{atmospheric_profile_model}-{bundle_target.from_datetime.strftime('%Y%m%d')}-{bundle_target.to_datetime.strftime('%Y%m%d')}"
                    if bundle_target.bundle_suffix is not None:
                        name += f"-{bundle_target.bundle_suffix}"

                    print(f"    Combined dataset has {len(combined_df)} rows")

                    if "csv" in bundle_target.output_formats:
                        path = os.path.join(bundle_target.dst_dir.root, name + ".csv")
                        combined_df.write_csv(path)
                        print(f"    Wrote CSV file to {path}")

                    if "parquet" in bundle_target.output_formats:
                        path = os.path.join(bundle_target.dst_dir.root, name + ".parquet")
                        combined_df.write_parquet(path)
                        print(f"    Wrote Parquet file to {path}")
