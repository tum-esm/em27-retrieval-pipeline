from typing import Any, Optional
import datetime
import os
import polars as pl
import tum_esm_utils


def load_results_directory(
    d: str,
    sensor_id: str,
    parse_dc_timeseries: bool = False,
    retrieval_job_output_suffix: Optional[str] = None,
) -> Optional[pl.DataFrame]:

    # 1. PARSE ABOUT.JSON

    about_path = os.path.join(d, "about.json")
    about = tum_esm_utils.files.load_json_file(about_path)
    context: dict[str, Any]
    if "session" not in about:
        raise Exception(f"Could not find a session in {about_path}")

    if "ctx" in about["session"]:
        context = about["session"]["ctx"]
    else:
        context = about["session"]

    if ("from_datetime" not in context) and ("date" not in context):
        raise Exception(f"Neither 'from_datetime' nor 'date' found in context: {context}")

    if "from_datetime" in context:
        from_datetime = tum_esm_utils.timing.parse_iso_8601_datetime(context["from_datetime"])
        to_datetime = tum_esm_utils.timing.parse_iso_8601_datetime(context["to_datetime"])
    else:
        date = datetime.datetime.strptime(context["date"], "%Y%m%d")
        from_datetime = datetime.datetime.combine(date, datetime.time.min)
        to_datetime = datetime.datetime.combine(date, datetime.time.max)

    location_id = context["location"]["location_id"]
    if "generationDate" in about:
        retrieval_time = datetime.datetime.strptime(
            about["generationDate"] + "T" + about["generationTime"], "%Y%m%dT%H:%M:%S"
        )
    else:
        retrieval_time = tum_esm_utils.timing.parse_iso_8601_datetime(about["generationTime"])

    assert sensor_id == context["sensor_id"]

    output_suffix: Optional[str] = None
    try:
        output_suffix = about["session"]["job_settings"]["output_suffix"]
    except KeyError:
        pass

    if output_suffix != retrieval_job_output_suffix:
        return None

    # 2. SEARCH FOR RESULTS FILE

    results_files = os.listdir(d)
    results_files = [f for f in results_files if ("comb" in f) and f.endswith(".csv")]
    if len(results_files) == 0:
        raise Exception(f"No results files found in {d}")
    if len(results_files) > 1:
        raise Exception(f"Multiple results files found in {d}: {results_files}")

    # 3. PARSE RESULTS FILE

    output_path = os.path.join(d, results_files[0])

    df = pl.read_csv(
        output_path,
        has_header=True,
        separator=",",
        schema_overrides={
            "UTC": pl.Datetime,
            " spectrum": pl.Utf8,
        }
    )
    df = df.rename({col: col.strip() for col in df.columns if col.strip() != col})

    df = df \
        .drop(list(
            set(["LocalTime", "JulianDate", "UTtimeh", "gndT", "SX"]).intersection(set(df.columns))
        ))

    if "UTC" not in df.columns:
        if "HHMMSS_ID" not in df.columns:
            raise Exception("Found neither 'UTC' nor 'HHMMSS_ID' in columns of file " + output_path)
        df = df.with_columns(
            pl.col("HHMMSS_ID").cast(pl.Utf8).map_elements(
                lambda hhmmss: datetime.datetime.
                combine(from_datetime.date(),
                        datetime.datetime.strptime(hhmmss, "%H%M%S").time()),
                return_dtype=pl.Datetime
            ).alias("UTC")
        )

    df = df.rename({
        "UTC": "utc",
        "gndP": "ground_pressure",
        "latdeg": "lat",
        "londeg": "lon",
        "altim": "alt",
        "appSZA": "sza",
        "azimuth": "azi",
    })

    df = df.with_columns(
        pl.col("utc").dt.replace_time_zone("UTC"),
        *[
            pl.col(col).cast(pl.Utf8).str.strip_chars(" ").cast(pl.Float64)
            for col in df.columns if col not in ["utc", "spectrum"]
        ],
    ).with_columns(
        pl.lit(retrieval_time).alias("retrieval_time").dt.replace_time_zone("UTC"),
        pl.lit(location_id).alias("location_id"),
    ).filter(
        pl.col("utc").ge(from_datetime.astimezone(tz=datetime.timezone.utc)) &
        pl.col("utc").le(to_datetime.astimezone(tz=datetime.timezone.utc))
    )

    if "spectrum" in df.columns:
        # remove leading and trailing whitespaces
        df = df.with_columns(pl.col("spectrum").cast(pl.Utf8).str.strip_chars(" "))

    if len(df) == 0:
        return None

    # 4. PARSE DC TIMESERIES

    if parse_dc_timeseries:
        spectrums: list[str] = []
        data: list[list[float]] = [[] for _ in range(16)]

        preprocessing_log_path = os.path.join(d, "analysis", "cal", "logfile.dat")
        if os.path.isfile(preprocessing_log_path):
            f = tum_esm_utils.files.load_file(preprocessing_log_path).strip(" \t\n")
            for line in f.split("\n"):
                parts = line.replace("\t", " ").split(" ")
                parts = [p for p in parts if p != ""]

                # 10 parts for normal preprocess6
                # 16 parts
                if len(parts) != 26:
                    continue

                spectrums.append(f"{parts[6]}_{parts[8]}SN.BIN")
                for i in range(16):
                    data[i].append(float(parts[i + 10]))

        preprocessing_df = pl.DataFrame({
            "spectrum": spectrums,
            "dcmean_fwd1": data[0],
            "dc_min_fwd1": data[1],
            "dc_max_fwd1": data[2],
            "dcvar_fwd1": data[3],
            "dcmean_bwd1": data[4],
            "dc_min_bwd1": data[5],
            "dc_max_bwd1": data[6],
            "dcvar_bwd1": data[7],
            "dcmean_fwd2": data[8],
            "dc_min_fwd2": data[9],
            "dc_max_fwd2": data[10],
            "dcvar_fwd2": data[11],
            "dcmean_bwd2": data[12],
            "dc_min_bwd2": data[13],
            "dc_max_bwd2": data[14],
            "dcvar_bwd2": data[15],
        })

        merged_df = df.join(preprocessing_df, on="spectrum", how="left")
        assert len(merged_df) == len(df)
        df = merged_df

    df = df.select("utc", pl.exclude("utc"))

    return df
