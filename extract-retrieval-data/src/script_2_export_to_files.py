import json
import pandas as pd
import mysql.connector

from src.utils.constants import PROJECT_DIR, CONFIG, DEFAULT_SPECTROMETERS, UNITS
from src.utils import functions


def as_csv(day_string, dataframes):
    # dataframes looks like this:
    # {
    #    "raw": {"co2": None, "ch4": None, "co": None},
    #    "filtered": {"co2": None, "ch4": None, "co": None},
    #     "meta": {
    #         "dfLocation": ...,
    #         "replacementDict": ...,
    #     }
    # }
    output_dfs = {}

    for gas in CONFIG["input"]["gases"]:
        df_corrected_inversion = (
            dataframes["filtered"][gas]
            .reset_index()
            .set_index(["ID_Location"])
            .join(
                dataframes["meta"]["dfLocation"].set_index(["ID_Location"])[
                    ["Direction"]
                ]
            )
            .reset_index()
        )

        # drop unused columns
        output_dfs[gas] = df_corrected_inversion.drop(
            columns=list(
                filter(
                    lambda c: c in df_corrected_inversion.columns,
                    [
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
                    ],
                )
            )
        )

    # use "Hour" column (timestamp) as index to merge data on
    merged_df = (
        pd.DataFrame(
            sorted(
                functions.unique(
                    functions.concat(
                        [
                            list(output_dfs[gas]["Hour"])
                            for gas in CONFIG["input"]["gases"]
                        ]
                    )
                )
            ),
            columns=["Hour"],
        )
        .applymap(lambda x: functions.hour_to_timestring(day_string, x))
        .set_index(["Hour"])
    )

    for gas in CONFIG["input"]["gases"]:
        output_dfs[gas]["Hour"] = output_dfs[gas]["Hour"].map(
            lambda x: functions.hour_to_timestring(day_string, x)
        )

        for spectrometer in [
            DEFAULT_SPECTROMETERS[l] for l in CONFIG["input"]["locations"]
        ]:
            df = (
                (
                    output_dfs[gas]
                    .loc[(output_dfs[gas]["ID_Spectrometer"] == spectrometer)]
                    .rename(
                        columns={
                            f"x{gas}_{UNITS[gas]}": f"{spectrometer}_x{gas}_{UNITS[gas]}_sc",
                        }
                    )
                )
                .set_index("Hour")
                .drop(columns=["ID_Spectrometer"])
            )
            merged_df = merged_df.merge(
                df,
                how="left",
                left_on="Hour",
                right_on="Hour",
            )

    if merged_df.empty:
        print(f"No filtered data for {day_string}")
    else:
        ACTUAL_LOCATIONS = {}
        for [location, sensor] in list(
            (df_corrected_inversion[["ID_Location", "ID_Spectrometer"]])
            .drop_duplicates()
            .values.tolist()
        ):
            ACTUAL_LOCATIONS.update({sensor: location})

        LOCATION_HEADER_ROWS = []
        for sensor in [DEFAULT_SPECTROMETERS[l] for l in CONFIG["input"]["locations"]]:
            if sensor in ACTUAL_LOCATIONS:
                LOCATION_HEADER_ROWS.append(
                    f"##    {sensor}: {ACTUAL_LOCATIONS[sensor]}"
                )
            else:
                LOCATION_HEADER_ROWS.append(f"##    {sensor}: unknown (no data)")

        db_connection = mysql.connector.connect(**CONFIG["authentication"]["mysql"])
        location_tuple = ", ".join([f'"{l}"' for l in CONFIG["input"]["locations"]])
        coordinates_query_result = pd.read_sql(
            f"""
            SELECT ID_Location, Coordinates_Longitude, Coordinates_Latitude, Coordinates_Altitude
            FROM location
            WHERE ID_Location in ({location_tuple})
            """,
            con=db_connection,
        ).values.tolist()
        db_connection.close()

        COORDINATES_HEADER_ROWS = []
        for row in coordinates_query_result:
            row[1:] = [format(x, ".3f").rjust(7, " ") for x in row[1:]]
            row[0] = row[0].rjust(5, " ")
            COORDINATES_HEADER_ROWS.append(
                f"##  {row[0]}: {row[1]}, {row[2]}, {row[3]}"
            )

        with open(f"{PROJECT_DIR}/data/csv-header-template.csv", "r") as template_file:
            with open(f"{PROJECT_DIR}/data/csv-out/{day_string}.csv", "w") as out_file:
                fillParameters = functions.replace_from_dict(
                    {
                        **dataframes["meta"]["replacementDict"],
                        "SENSOR_LOCATIONS": "\n".join(LOCATION_HEADER_ROWS),
                        "LOCATION_COORDINATES": "\n".join(COORDINATES_HEADER_ROWS),
                    }
                )
                out_file.writelines(
                    list(map(fillParameters, template_file.readlines()))
                )
                merged_df.fillna("NaN").reset_index().rename(
                    columns={"Hour": "year_day_hour"}
                ).set_index(["year_day_hour"]).to_csv(out_file)


def as_json(day_string, dataframes):
    # dataframes looks like this:
    # {
    #    "raw": {"co2": None, "ch4": None, "co": None},
    #    "filtered": {"co2": None, "ch4": None, "co": None},
    #     "meta": {
    #         "dfLocation": ...,
    #         "replacementDict": ...,
    #     }
    # }
    output_dfs = {"raw": {}, "filtered": {}}

    if dataframes is None:
        return

    for gas in CONFIG["input"]["gases"]:
        for case in ["raw", "filtered"]:

            df_corrected_website = dataframes[case][gas].drop(
                [
                    "fvsi",
                    "sia_AU",
                    "asza_deg",
                    "xo2_error",
                    "pout_hPa",
                    "pins_mbar",
                    "column_o2",
                    "column_h2o",
                    "column_air",
                    "xair",
                    "xh2o_ppm",
                ],
                axis=1,
            )

            df_corrected_website = (
                df_corrected_website.reset_index()
                .set_index(["ID_Location"])
                .join(
                    dataframes["meta"]["dfLocation"].set_index(["ID_Location"])[
                        ["Direction"]
                    ]
                )
                .reset_index()
            )
            columns_to_drop = ["Date", "Direction"]
            if (case == "website-filtered") and (not df_corrected_website.empty):
                columns_to_drop += ["year", "month", "flag"]
                df_corrected_website.reset_index()
                df_corrected_website["Hour"] = df_corrected_website["Hour"].round(3)
            df_corrected_website.rename(
                columns={
                    "Hour": "hour",
                    "ID_Location": "location",
                    "ID_Spectrometer": "spectrometer",
                    f"x{gas}_{UNITS[gas]}": "x",
                },
                inplace=True,
            )
            df_corrected_website = (
                df_corrected_website.drop(columns=columns_to_drop)
                .set_index(["hour"])
                .sort_index()
            )

            output_dfs[case][gas] = df_corrected_website

    # output_dfs = {
    #    "raw": {"co2": None, "ch4": None, "co": None},
    #    "filtered": {"co2": None, "ch4": None, "co": None},
    # }

    output_jsons = []
    # each json element = {
    #     "sensor": *,
    #     "location": *,
    #     "gas": *,
    #     "date": "2021-08-01",
    #     "filteredCount": *,
    #     "filteredTimeseries": {"xs": *, "ys": *},
    #     "rawCount": *,
    #     "rawTimeseries": {"xs": *, "ys": *},
    #     "flagCount": *,
    #     "flagTimeseries": {"xs": *, "ys": *},
    # }

    spectrometers = functions.unique(
        functions.concat(
            list(output_dfs["raw"][gas]["spectrometer"])
            for gas in CONFIG["input"]["gases"]
        )
    )

    for gas in CONFIG["input"]["gases"]:
        for location in CONFIG["input"]["locations"]:
            for spectrometer in spectrometers:

                def apply_local_filter(df, remove_by_flag=False):
                    a = df.loc[(df["location"] == location)]
                    b = a.loc[(a["spectrometer"] == spectrometer)]
                    c = b.loc[(b["flag"] != 0)] if remove_by_flag else b
                    return c.sort_index().reset_index()

                df_filtered = apply_local_filter(output_dfs["filtered"][gas])
                df_raw = apply_local_filter(output_dfs["raw"][gas])
                df_flag = apply_local_filter(
                    output_dfs["raw"][gas], remove_by_flag=True
                )

                def round_df_column(c):
                    return list(
                        map(
                            lambda x: round(x, {"co2": 3, "ch4": 5, "co": 3}[gas]),
                            list(c),
                        )
                    )

                if df_raw["x"].count() > 0:
                    output_jsons.append(
                        {
                            "spectrometer": spectrometer,
                            "location": location.replace("GRÄ", "GRAE"),
                            "gas": gas,
                            "date": f"{day_string[:4]}-{day_string[4:6]}-{day_string[6:]}",
                            "filteredCount": df_filtered.shape[0],
                            "filteredTimeseries": {
                                "xs": round_df_column(df_filtered["hour"]),
                                "ys": round_df_column(df_filtered["x"]),
                            },
                            "rawCount": df_raw.shape[0],
                            "rawTimeseries": {
                                "xs": round_df_column(df_raw["hour"]),
                                "ys": round_df_column(df_raw["x"]),
                            },
                            "flagCount": df_flag.shape[0],
                            "flagTimeseries": {
                                "xs": round_df_column(df_flag["hour"]),
                                "ys": round_df_column(df_flag["flag"]),
                            },
                        }
                    )

    with open(f"{PROJECT_DIR}/data/json-out/{day_string}.json", "w") as f:
        json.dump(output_jsons, f, indent=2)