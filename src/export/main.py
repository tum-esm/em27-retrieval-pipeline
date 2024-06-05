import datetime
import os
import json
import sys
import polars as pl
import rich.progress
import em27_metadata
import tum_esm_utils

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../.."))
from src import types, utils, export


def run() -> None:
    config = types.Config.load()
    assert config.export_targets is not None, "no export config found"
    assert len(config.export_targets) > 0, "no export targets found"

    em27_metadata_interface = utils.metadata.load_local_em27_metadata_interface(
    )
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

    for i, output_merging_target in enumerate(config.export_targets):
        print(f"\nprocessing output merging target #{i+1}")
        print(json.dumps(output_merging_target.model_dump(), indent=4))
        assert (
            output_merging_target.campaign_id
            in em27_metadata_interface.campaigns.campaign_ids
        ), f"unknown campaign_id {output_merging_target.campaign_id}"

        campaign = next(
            campaign for campaign in em27_metadata_interface.campaigns.root
            if campaign.campaign_id == output_merging_target.campaign_id
        )

        dates: list[datetime.date] = tum_esm_utils.timing.date_range(
            from_date=campaign.from_datetime.date(),
            to_date=min((
                datetime.datetime.now(tz=datetime.UTC) -
                datetime.timedelta(days=1)
            ).date(), campaign.to_datetime.date())
        )
        print(
            f"Exporting data from {dates[0]} to {dates[-1]} " +
            f"({len(dates)} dates)"
        )

        dst_dir = os.path.join(
            output_merging_target.dst_dir.root,
            f"em27-retrieval-pipeline-v{utils.functions.get_pipeline_version()}-exports",
            f"{output_merging_target.campaign_id}",
            output_merging_target.retrieval_algorithm,
            output_merging_target.atmospheric_profile_model,
        )
        if not os.path.exists(dst_dir):
            print("Creating output directory at", dst_dir)
            os.makedirs(dst_dir)
        else:
            print("Output directory already exists at", dst_dir)

        print("Removing old outputs (output dir/*.csv)")
        os.system(f"rm -f {dst_dir}/*.csv")

        with rich.progress.Progress() as progress:
            task = progress.add_task("processing dataframes", total=len(dates))

            for date in dates[::-1]:
                sensor_data_contexts: list[em27_metadata.types.SensorDataContext
                                          ] = []

                # get all sensor data contexts for this campaign's sensors
                for sid in campaign.sensor_ids:
                    sensor_data_contexts += em27_metadata_interface.get(
                        sid,
                        from_datetime=datetime.datetime.combine(
                            date,
                            datetime.time.min,
                            tzinfo=datetime.timezone.utc
                        ),
                        to_datetime=datetime.datetime.combine(
                            date,
                            datetime.time.max,
                            tzinfo=datetime.timezone.utc
                        ),
                    )

                # only consider data at campaign locations
                # sdc = sensor data context
                sdcs = list(
                    filter(
                        lambda ctx: ctx.location.location_id in campaign.
                        location_ids,
                        sensor_data_contexts,
                    )
                )
                sdcs_with_data: list[em27_metadata.types.SensorDataContext] = []

                dataframes: list[pl.DataFrame] = []
                found_data_count: int = 0

                for sdc in sdcs:
                    try:
                        df = export.dataframes.get_sensor_dataframe(
                            config, sdc, output_merging_target
                        )
                    except AssertionError:
                        continue

                    postprocessed_df = export.dataframes.post_process_dataframe(
                        df=df,
                        sampling_rate=output_merging_target.sampling_rate,
                        max_interpolation_gap_seconds=output_merging_target.
                        max_interpolation_gap_seconds,
                    )
                    if len(postprocessed_df) > 1:
                        sdcs_with_data.append(sdc)
                        found_data_count += 1
                        dataframes.append(postprocessed_df)

                if found_data_count > 0:
                    progress.console.print(
                        f"{date}: {found_data_count} sensor(s) with data"
                    )

                    merged_df = export.dataframes.merge_dataframes(dataframes)

                    # save merged dataframe to csv
                    filename = os.path.join(
                        dst_dir,
                        (
                            f"{output_merging_target.campaign_id}_" +
                            f"export_{date.strftime('%Y%m%d')}.csv"
                        ),
                    )
                    with open(filename, "w") as f:
                        f.write(
                            export.header.get_header(
                                em27_metadata_interface,
                                campaign,
                                sdcs_with_data,
                                output_merging_target,
                            )
                        )
                        f.write(
                            merged_df.write_csv(
                                null_value="NaN",
                                include_header=True,
                                float_precision=9,
                            )
                        )

                progress.advance(task)


if __name__ == "__main__":
    run()
