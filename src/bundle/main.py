import datetime
import os
import re
import sys
import polars as pl
import em27_metadata
import tum_esm_utils

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../.."))
from src import types, utils
from .load_results import load_results_directory


def run() -> None:
    config = types.Config.load()
    assert config.export_targets is not None, "no export config found"
    assert len(config.export_targets) > 0, "no export targets found"

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
        print(f"Processing bundle target #{i+1}")
        print(f"Bundle target: {bundle_target.model_dump_json(indent=4)}")

        for retrieval_algorithm in bundle_target.retrieval_algorithms:
            for atmospheric_profile_model in bundle_target.atmospheric_profile_models:
                for sensor_id in bundle_target.sensor_ids:
                    dfs: list[pl.DataFrame] = []

                    d = os.path.join(
                        config.general.data.results.root, retrieval_algorithm,
                        atmospheric_profile_model, sensor_id, "successful"
                    )
                    print(f"Sensor {sensor_id}: looking for files in {d}")

                    results_pattern = re.compile(r"^\d{8}(_\d{8}_\d{8})?(_.*)?$")
                    all_results = [
                        r for r in os.listdir(d)
                        if os.path.isdir(os.path.join(d, r)) and results_pattern.match(r)
                    ]
                    print(f"  Found {len(all_results)} results directories")
                    if bundle_target.retrieval_job_output_suffix is None:
                        matching_results = all_results
                    else:
                        matching_results = [
                            r for r in all_results
                            if r.endswith(bundle_target.retrieval_job_output_suffix)
                        ]
                        print(
                            f"  Found {len(matching_results)} results directories matching the output suffix"
                        )

                    for result in matching_results:
                        df = load_results_directory(
                            os.path.join(d, result),
                            sensor_id,
                            parse_dc_timeseries=(
                                bundle_target.parse_dc_timeseries and
                                (retrieval_algorithm == "proffast-2.4")
                            ),
                            retrieval_job_output_suffix=bundle_target.retrieval_job_output_suffix,
                        )
                        if df is not None:
                            dfs.append(df)

                    combined_df = pl.concat(dfs).sort("utc")

                    name = f"em27-retrieval-bundle-{sensor_id}-{retrieval_algorithm}-{atmospheric_profile_model}-{bundle_target.from_datetime.strftime('%Y%m%d')}-{bundle_target.to_datetime.strftime('%Y%m%d')}"
                    if bundle_target.bundle_suffix is not None:
                        name += f"-{bundle_target.bundle_suffix}"

                    if "csv" in bundle_target.output_formats:
                        path = os.path.join(bundle_target.dst_dir, name + ".csv")
                        combined_df.write_csv(path)
                        print(f"  Wrote CSV file to {path}")

                    if "parquet" in bundle_target.output_formats:
                        path = os.path.join(bundle_target.dst_dir, name + ".parquet")
                        combined_df.write_parquet(path)
                        print(f"  Wrote Parquet file to {path}")
