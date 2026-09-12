import datetime
import os
import re
import sys
from typing import Optional

import polars as pl
import tqdm
import tum_esm_utils

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../.."))
from src import types, utils, em27_metadata

from .load_results import load_results_directory


def run(
    config: Optional[types.Config] = None,
    em27_metadata_interface: Optional[em27_metadata.interfaces.EM27MetadataInterface] = None,
) -> None:
    if config is None:
        print("Loading configuration")
        config = types.Config.load()

    assert config.bundle_exports is not None, "no bundle targets found"
    assert len(config.bundle_exports) > 0, "no bundle targets found"

    # TODO: refactor metadata loading
    if em27_metadata_interface is None:
        em27_metadata_interface = utils.metadata.load_local_em27_metadata_interface()
        if em27_metadata_interface is not None:
            print("Found local metadata")
        else:  # pragma: no cover
            print("Did not find local metadata -> fetching metadata from GitHub")
            assert config.metadata.source == "github", "Remote metadata not configured"
            assert config.metadata.github_repository is not None, (
                "This should have been caught earlier"
            )
            em27_metadata_interface = em27_metadata.load_from_github(
                github_repository=config.metadata.github_repository,
                access_token=config.metadata.github_access_token,
            )
            print("Successfully fetched metadata from GitHub")

    for i, bundle_export_config in enumerate(config.bundle_exports):
        print(f"Processing bundle export #{i + 1}")
        print(f"Bundle export config: {bundle_export_config.model_dump_json(indent=4)}")

        for retrieval_algorithm in bundle_export_config.retrieval_algorithms:
            for atmospheric_profile_model in bundle_export_config.atmospheric_profile_models:
                if (retrieval_algorithm == "proffast-1.0") and (
                    atmospheric_profile_model == "GGG2020"
                ):
                    print("Skipping proffast-1.0/GGG2020 as it is not supported")
                    continue
                print(f"Processing {retrieval_algorithm}/{atmospheric_profile_model}")
                for sensor_id in bundle_export_config.sensor_ids:
                    dfs: list[pl.DataFrame] = []

                    d = os.path.join(
                        config.data.results.path.root,
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

                    if bundle_export_config.retrieval_job_output_suffix is None:
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
                            and r.endswith(bundle_export_config.retrieval_job_output_suffix)
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
                                    bundle_export_config.from_datetime_parsed.date()
                                    <= datetime.datetime.strptime(r[:8], "%Y%m%d").date()
                                )
                                and (
                                    datetime.datetime.strptime(r[:8], "%Y%m%d").date()
                                    <= bundle_export_config.to_datetime_parsed.date()
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
                            parse_dc_timeseries=bundle_export_config.parse_dc_timeseries,
                            parse_retrieval_diagnostics=bundle_export_config.parse_retrieval_diagnostics,
                            retrieval_job_output_suffix=bundle_export_config.retrieval_job_output_suffix,
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
                                c.from_datetime_parsed <= utcs[i] <= c.to_datetime_parsed
                            ):
                                matching_campaign_ids[i] += f"+{c.campaign_id}"
                    matching_campaign_ids = [s.lstrip("+") for s in matching_campaign_ids]
                    combined_df = combined_df.with_columns(
                        pl.Series("campaign_ids", matching_campaign_ids)
                    )

                    # Attach a columns "event_description" and "event_data_quality_flag" to the data
                    matching_event_descriptions: list[str] = ["" for _ in range(len(combined_df))]
                    matching_event_flags: list[int] = [0 for _ in range(len(combined_df))]
                    utcs = combined_df["utc"].to_list()
                    location_ids = combined_df["location_id"].to_list()
                    for e in em27_metadata_interface.events.root:
                        if sensor_id not in e.sensor_ids:
                            continue
                        for i in range(len(combined_df)):
                            if e.from_datetime_parsed <= utcs[i] <= e.to_datetime_parsed:
                                matching_event_descriptions[i] += f"; {e.description}"
                                if not e.data_is_usable:
                                    matching_event_flags[i] = 1
                    matching_event_descriptions = [
                        s.strip("; ") for s in matching_event_descriptions
                    ]
                    combined_df = combined_df.with_columns(
                        pl.Series("event_description", matching_event_descriptions),
                        pl.Series("event_data_quality_flag", matching_event_flags),
                    )

                    name = f"em27-retrieval-bundle-{sensor_id}-{retrieval_algorithm}-{atmospheric_profile_model}-{bundle_export_config.from_datetime_parsed.strftime('%Y%m%d')}-{bundle_export_config.to_datetime_parsed.strftime('%Y%m%d')}"
                    if bundle_export_config.bundle_suffix is not None:
                        name += f"-{bundle_export_config.bundle_suffix}"

                    print(f"    Combined dataset has {len(combined_df)} rows")

                    if "csv" in bundle_export_config.output_formats:
                        path = os.path.join(bundle_export_config.dst_dir.root, name + ".csv")
                        combined_df.write_csv(path)
                        print(f"    Wrote CSV file to {path}")

                    if "parquet" in bundle_export_config.output_formats:
                        path = os.path.join(bundle_export_config.dst_dir.root, name + ".parquet")
                        combined_df.write_parquet(path)
                        print(f"    Wrote Parquet file to {path}")
