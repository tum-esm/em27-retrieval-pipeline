import os
import json
import sys
import polars as pl
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

    for output_merging_target in config.output_merging_targets:
        assert (
            output_merging_target.campaign_id in em27_metadata.campaign_ids
        ), f"unknown campaign_id {output_merging_target.campaign_id}"

        print(output_merging_target)

        campaign = next(
            campaign
            for campaign in em27_metadata.campaigns
            if campaign.campaign_id == output_merging_target.campaign_id
        )

        for date in range(int(campaign.from_date), int(campaign.to_date) + 1):
            if not tum_esm_utils.text.is_date_string(str(date)):
                continue

            print(date)

            dfs: pl.DataFrame = []
            found_data_count: int = 0
            for campaign_station in campaign.stations:
                try:
                    sensor_data_context = em27_metadata.get(
                        campaign_station.sensor_id, str(date)
                    )
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

            if found_data_count == 0:
                continue

            merged_df = procedures.merged_outputs.merge_dataframes(dfs)

            # save merged dataframe to csv
            filename = os.path.join(
                output_merging_target.dst_dir,
                f"{output_merging_target.campaign_id}_em27_export_{date}.csv",
            )
            # with open(filename, "w") as f:
            #    f.write(procedures.merged_outputs.get_metadata())
            merged_df.write_csv(filename, null_value="NaN", has_header=True)


if __name__ == "__main__":
    run()
