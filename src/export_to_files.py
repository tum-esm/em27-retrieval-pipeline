import pandas as pd
import os
from .helpers.utils import unique, hour_to_timestring, replace_from_dict


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_OUT_DIR = f"{PROJECT_DIR}/data/csv-out"


def as_csv(date_string, dataframes):
    # dataframes looks like this:
    # {
    #    "raw": {"xco2": None, "xch4": None, "xco": None},
    #    "filtered": {"xco2": None, "xch4": None, "xco": None},
    #     "meta": {
    #         "dfLocation": ...,
    #         "replacementDict": ...,
    #     }
    # }
    filtered_dataframes = dataframes["filtered"]
    output_dfs = {}

    # TODO: Use gases from config.json
    for gas in ["xco2", "xch4", "xco"]:
        df_corrected_inversion = (
            df_corrected_inversion.reset_index()
            .set_index(["ID_Location"])
            .join(
                dataframes["meta"]["dfLocation"].set_index(["ID_Location"])[
                    ["Direction"]
                ]
            )
            .reset_index()
        )

        columns_to_drop = [
            "ID_Location",
            "Direction",
            "xh2o_ppm",
            "fvsi",
            "sia_AU",
            "asza_deg",
            "flag",
            "pout_hPa",
            "pins_mbar",
            "xo2_error",
            "column_o2",
            "column_h2o",
            "column_air",
            "xair",
            "month",
            "year",
            "Date",
        ]

        df_corrected_inversion = df_corrected_inversion.drop(
            columns=[c for c in columns_to_drop if c in df_corrected_inversion.columns]
        )

        output_dfs[gas] = df_corrected_inversion

    inversion_hours = unique(
        list(output_dfs["xco2"]["Hour"]) + list(output_dfs["xch4"]["Hour"])
    )
    inversion_hour_df = (
        pd.DataFrame(sorted(inversion_hours), columns=["Hour"])
        .applymap(lambda x: hour_to_timestring(date_string, x))
        .set_index(["Hour"])
    )

    merged_df = inversion_hour_df

    # TODO: Use gases from config.json
    for gas in ["xco2", "xch4", "xco"]:
        output_dfs[gas]["Hour"] = output_dfs[gas]["Hour"].map(
            lambda x: hour_to_timestring(date_string, x)
        )

        # TODO: Use spectrometers from config.json
        # TODO: Use locations instead of spectrometers
        for spectrometer in ["mb86", "mc15", "md16", "me17"]:
            df = (
                output_dfs[gas]
                .loc[(output_dfs[gas]["ID_Spectrometer"] == spectrometer)]
                .rename(
                    columns={
                        f"{gas}_ppm": f"{spectrometer[:2]}_{gas}_sc",
                    }
                )
            )
            merged_df = merged_df.merge(
                df.set_index("Hour").drop(columns=["ID_Spectrometer"]),
                how="left",
                left_on="Hour",
                right_on="Hour",
            )

    with open(f"{PROJECT_DIR}/data/csv-header-template.csv", "r") as template_file:
        with open(f"{CSV_OUT_DIR}/{date_string}.csv", "w") as out_file:
            fillParameters = replace_from_dict(filtered_dataframes["replacement_dict"])
            out_file.writelines(list(map(fillParameters, template_file.readlines())))
            merged_df.fillna("NaN").reset_index().rename(
                columns={"Hour": "year_day_hour"}
            ).set_index(["year_day_hour"]).to_csv(out_file)


def as_json():
    # TODO: Create tmp directory
    # TODO: Save raw and filtered CSVs
    # TODO: Convert CSVs to JSON
    # TODO: Remove tmp directory
    pass
