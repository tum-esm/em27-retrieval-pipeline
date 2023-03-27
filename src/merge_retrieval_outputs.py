from datetime import datetime
import os
import json
import sys
import polars as pl
import rich.progress
import tum_esm_em27_metadata
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
sys.path.append(PROJECT_DIR)

from src import custom_types, procedures


def run() -> None:
    with open(os.path.join(PROJECT_DIR, "config", "config.json"), "r") as f:
        config = custom_types.Config(**json.load(f))

    em27_metadata = tum_esm_em27_metadata.load_from_github(
        **config.general.location_data.dict()
    )

    for i, output_merging_target in enumerate(config.output_merging_targets):
        print(f"\nprocessing output merging target #{i}")
        print(json.dumps(output_merging_target.dict(), indent=4))
        assert (
            output_merging_target.campaign_id in em27_metadata.campaign_ids
        ), f"unknown campaign_id {output_merging_target.campaign_id}"

        campaign = next(
            campaign
            for campaign in em27_metadata.campaigns
            if campaign.campaign_id == output_merging_target.campaign_id
        )

        to_date = min(datetime.utcnow().strftime("%Y%m%d"), campaign.to_date)
        date_range = [
            d
            for d in range(int(campaign.from_date), int(to_date) + 1)
            if tum_esm_utils.text.is_date_string(str(d))
        ]

        with rich.progress.Progress() as progress:
            task = progress.add_task("processing dataframes", total=len(date_range))

            for date in date_range:
                sensor_data_contexts: dict[
                    str, tum_esm_em27_metadata.types.SensorDataContext
                ] = {}
                dfs: pl.DataFrame = []
                found_data_count: int = 0
                for campaign_station in campaign.stations:
                    try:
                        sensor_data_context = em27_metadata.get(
                            campaign_station.sensor_id, str(date)
                        )
                        sensor_data_contexts[
                            campaign_station.sensor_id
                        ] = sensor_data_context
                        assert (
                            campaign_station.default_location_id
                            == sensor_data_context.location.location_id
                        )
                        df = procedures.merged_outputs.get_sensor_dataframe(
                            config,
                            sensor_data_context,
                            output_merging_target,
                        )
                        dfs.append(
                            procedures.merged_outputs.post_process_dataframe(
                                df,
                                output_merging_target.sampling_rate,
                            )
                        )
                        found_data_count += 1
                    except AssertionError:
                        dfs.append(
                            procedures.merged_outputs.get_empty_sensor_dataframe(
                                campaign_station.sensor_id,
                                output_merging_target,
                            )
                        )

                if found_data_count > 0:
                    progress.console.print(
                        f"{date}: {found_data_count} sensor(s) with data"
                    )
                    merged_df = procedures.merged_outputs.merge_dataframes(dfs)

                    # save merged dataframe to csv
                    filename = os.path.join(
                        output_merging_target.dst_dir,
                        f"{output_merging_target.campaign_id}_em27_export_{date}.csv",
                    )
                    with open(filename, "w") as f:
                        f.write(
                            procedures.merged_outputs.get_metadata(
                                campaign,
                                sensor_data_contexts,
                                output_merging_target,
                            )
                            + "\n"
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
