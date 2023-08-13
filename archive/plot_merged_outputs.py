from datetime import datetime
import os
import polars as pl
import matplotlib.pyplot as plt
from plotting_utils import plot, save_plot
from tailwind_colors import TAILWIND_COLORS

raw = "/Users/moritz/Documents/research/automated-retrieval-pipeline/data/testing/merging/raw"
merged = "/Users/moritz/Documents/research/automated-retrieval-pipeline/data/testing/merging/merged"

serial_numbers = {
    "ma": "061",
    "mb": "086",
    "mc": "115",
}
colors = {
    "co2": {
        "ma": TAILWIND_COLORS.RED_400,
        "mb": TAILWIND_COLORS.AMBER_400,
        "mc": TAILWIND_COLORS.GREEN_400,
    },
    "ch4": {
        "ma": TAILWIND_COLORS.RED_600,
        "mb": TAILWIND_COLORS.AMBER_600,
        "mc": TAILWIND_COLORS.GREEN_600,
    },
}

for date in ["20210329", "20210330"]:
    merged_filename = f"muccnet_em27_export_{date}.csv"
    merged_df = pl.read_csv(
        os.path.join(merged, merged_filename),
        comment_char="#",
        dtypes={"utc": pl.Datetime},
    )

    fig, _ = plt.subplots(
        3,
        2,
        gridspec_kw={"height_ratios": [2, 2, 2], "hspace": 0.5},
        figsize=(15, 10),
    )
    fig.suptitle(
        f"Raw and postprocessed sensor data at {date}",
        fontsize=16,
        y=0.94,
    )

    for i, sensor_id in enumerate(["ma", "mb", "mc"]):
        raw_filename = f"{sensor_id}/proffast-2.2-outputs/successful/{date}/comb_invparms_{sensor_id}_SN{serial_numbers[sensor_id]}_{date[2:]}-{date[2:]}.csv"
        raw_df = pl.read_csv(
            os.path.join(raw, raw_filename), dtypes={"UTC": pl.Datetime}
        )

        for j, gas in enumerate(["co2", "ch4"]):

            print(f"plotting {sensor_id}/{date}/{gas}")

            with plot(
                subplot_row_count=3,
                subplot_col_count=2,
                subplot_number=(i * 2) + j + 1,
                xlabel="UTC time",
                ylabel=f"X{gas.upper()} [ppm]",
                title=f"X{gas.upper()} of {sensor_id}",
                xaxis_scale="hours",
            ) as p:
                xs_raw = raw_df.get_column("UTC")
                ys_raw = raw_df.get_column(f" X{gas.upper()}")
                p.scatter(
                    xs_raw,
                    ys_raw,
                    s=1,
                    color=colors[gas][sensor_id],
                    alpha=0.35,
                )

                xs_smooth = merged_df.get_column("utc")
                ys_smooth = merged_df.get_column(f"{sensor_id}_x{gas}")
                p.plot(
                    xs_smooth,
                    ys_smooth,
                    linewidth=1.5,
                    color=colors[gas][sensor_id],
                    alpha=1,
                    linestyle="-",
                )

    save_plot(f"{merged}/{merged_filename[:-4]}.png")
    plt.close()

    # plot merged data from only half and hour (11.00 - 11.30)
    fig, _ = plt.subplots(
        1,
        2,
        gridspec_kw={"height_ratios": [1], "hspace": 1, "wspace": 0.25},
        figsize=(10, 3),
    )
    fig.suptitle(f"Postprocessed sensor data at {date}", fontsize=12)

    detailed_merged_df = merged_df.filter(
        (
            pl.col("utc")
            > datetime(
                year=int(date[:4]),
                month=int(date[4:6]),
                day=int(date[6:]),
                hour=11,
                minute=0,
                second=0,
            )
        )
        & (
            pl.col("utc")
            < datetime(
                year=int(date[:4]),
                month=int(date[4:6]),
                day=int(date[6:]),
                hour=11,
                minute=30,
                second=0,
            )
        )
    )

    for j, gas in enumerate(["co2", "ch4"]):
        with plot(
            subplot_row_count=1,
            subplot_col_count=2,
            subplot_number=j + 1,
            xlabel="UTC time",
            ylabel=f"X{gas.upper()} [ppm]",
            title=f"X{gas.upper()}",
            xaxis_scale="minutes",
        ) as p:
            for i, sensor_id in enumerate(["ma", "mb", "mc"]):
                xs_smooth = detailed_merged_df.get_column("utc")
                ys_smooth = detailed_merged_df.get_column(f"{sensor_id}_x{gas}")
                p.scatter(
                    xs_smooth,
                    ys_smooth,
                    s=4,
                    color=colors[gas][sensor_id],
                    alpha=1,
                )

    save_plot(f"{merged}/{merged_filename[:-4]}-detailed.png")
    plt.close()
