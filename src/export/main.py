import datetime
import os
import json
import sys
import polars as pl
import rich.progress
import em27_metadata
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=3
)
sys.path.append(_PROJECT_DIR)

from src import utils, export


def run() -> None:
    config = utils.config.Config.load()
    assert config.export is not None, "no export config found"
    assert len(config.export.targets) > 0, "no export targets found"

    em27_metadata_storage = em27_metadata.load_from_github(
        **config.general.location_data.model_dump()
    )

    for i, output_merging_target in enumerate(config.export.targets):
        print(f"\nprocessing output merging target #{i+1}")
        print(json.dumps(output_merging_target.model_dump(), indent=4))
        assert (
            output_merging_target.campaign_id
            in em27_metadata_storage.campaign_ids
        ), f"unknown campaign_id {output_merging_target.campaign_id}"

        campaign = next(
            campaign for campaign in em27_metadata_storage.campaigns
            if campaign.campaign_id == output_merging_target.campaign_id
        )

        from_date = campaign.from_datetime.date()
        to_date = min(
            datetime.datetime.utcnow().date(), campaign.to_datetime.date()
        )

        dates: list[datetime.date] = []
        current_date = from_date
        while current_date <= to_date:
            dates.append(current_date)
            current_date += datetime.timedelta(days=1)

        print("Removing old outputs")
        os.system(
            "rm -f " + os.path.join(
                output_merging_target.dst_dir,
                f"{output_merging_target.campaign_id}_em27_export" +
                f"_v{export.header.get_pipeline_version()}"
                f"_*.csv",
            )
        )

        with rich.progress.Progress() as progress:
            task = progress.add_task("processing dataframes", total=len(dates))

            for date in dates:
                sensor_data_contexts: list[em27_metadata.types.SensorDataContext
                                          ] = []

                # get all sensor data contexts for this campaign's sensors
                for sid in campaign.sensor_ids:
                    sensor_data_contexts += em27_metadata_storage.get(
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

                ctx_dataframes: list[pl.DataFrame] = []
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
                        ctx_dataframes.append(postprocessed_df)

                if found_data_count > 0:
                    progress.console.print(
                        f"{date}: {found_data_count} sensor(s) with data"
                    )

                    merged_df = export.dataframes.merge_dataframes(
                        ctx_dataframes
                    )

                    # save merged dataframe to csv
                    filename = os.path.join(
                        output_merging_target.dst_dir,
                        f"{output_merging_target.campaign_id}_em27_export" +
                        f"_v{export.header.get_pipeline_version()}"
                        f"_{date.strftime('%Y%m%d')}.csv",
                    )
                    with open(filename, "w") as f:
                        f.write(
                            export.header.get_header(
                                em27_metadata_storage,
                                campaign,
                                sdcs_with_data,
                                output_merging_target,
                            )
                        )
                        f.write(
                            merged_df.write_csv(
                                null_value="NaN",
                                has_header=True,
                                float_precision=9,
                            )
                        )

                progress.advance(task)


if __name__ == "__main__":
    run()
