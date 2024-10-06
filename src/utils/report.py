from typing import Literal
import datetime
import re
import os
import em27_metadata
import polars as pl
import tum_esm_utils
import rich.console
import rich.progress
from src import types
from .text import get_coordinates_slug, replace_regex_placeholders
from .functions import sdc_covers_the_full_day


def _ggg2014_profiles_exists(
    path: str,
    lat: float,
    lon: float,
    date: datetime.date,
) -> str:
    date_string = date.strftime("%Y%m%d")
    coords_string = get_coordinates_slug(lat, lon)
    return "✅" if os.path.isfile(
        os.path.join(path, "GGG2014", f"{date_string}_{coords_string}.map")
    ) else "-"


def _ggg2020_profiles_exists(
    path: str,
    lat: float,
    lon: float,
    date: datetime.date,
) -> str:
    date_string = date.strftime("%Y%m%d")
    coords_string = get_coordinates_slug(lat, lon)
    return "✅" if all([
        os.path.isfile(os.path.join(path, "GGG2020", f"{date_string}{h:02d}_{coords_string}.map"))
        for h in range(0, 22, 3)
    ]) else "-"


def _count_ifg_datapoints(
    path: str,
    sensor_id: str,
    date: datetime.date,
) -> int:

    try:
        return int(
            tum_esm_utils.shell.run_shell_command(
                f"ls -f {os.path.join(path, sensor_id, date.strftime('%Y%m%d'))} | wc -l"
            )
        )
    except Exception:
        return 0


def _count_ground_pressure_datapoints(
    config: types.Config,
    sensor_id: str,
    date: datetime.date,
) -> int:
    _, file_pattern = replace_regex_placeholders(
        config.general.data.ground_pressure.file_regex, sensor_id, date
    )
    d = os.path.join(config.general.data.ground_pressure.path.root, sensor_id)
    all_files = os.listdir(d)
    matching_files = [f for f in all_files if file_pattern.match(f) is not None]
    line_count = 0
    for file in matching_files:
        with open(os.path.join(d, file), "r") as f:
            line_count += len(f.readlines())
    return line_count


def _check_retrieval_output(
    config: types.Config,
    date: datetime.date,
    sdc: em27_metadata.types.SensorDataContext,
    retrieval_algorithm: Literal[
        "proffast-1.0",
        "proffast-2.2",
        "proffast-2.3",
        "proffast-2.4",
    ],
    atmospheric_model: Literal[
        "GGG2014",
        "GGG2020",
    ],
) -> Literal["✅", "❌", "-"]:
    output_folder_slug = date.strftime("%Y%m%d")
    if not sdc_covers_the_full_day(sdc):
        output_folder_slug += max(
            sdc.from_datetime,
            datetime.datetime.combine(date, datetime.time.min, tzinfo=datetime.timezone.utc),
        ).strftime("_%H%M%S")
        output_folder_slug += min(
            sdc.to_datetime,
            datetime.datetime.combine(date, datetime.time.max, tzinfo=datetime.timezone.utc),
        ).strftime("_%H%M%S")

    success_path = os.path.join(
        config.general.data.results.root,
        retrieval_algorithm,
        atmospheric_model,
        sdc.sensor_id,
        "successful",
        output_folder_slug,
    )
    failed_path = os.path.join(
        config.general.data.results.root,
        retrieval_algorithm,
        atmospheric_model,
        sdc.sensor_id,
        "failed",
        output_folder_slug,
    )
    if os.path.isdir(success_path):
        return "✅"
    elif os.path.isdir(failed_path):
        return "❌"
    else:
        return "-"


def export_data_report(
    config: types.Config,
    em27_metadata_interface: em27_metadata.interfaces.EM27MetadataInterface,
    console: rich.console.Console,
) -> None:
    for sensor in em27_metadata_interface.sensors.root:
        from_datetimes: list[datetime.datetime] = []
        to_datetimes: list[datetime.datetime] = []
        location_ids: list[str] = []
        interferograms: list[int] = []
        ground_pressure: list[int] = []
        ggg2014_profiles: list[str] = []
        ggg2020_profiles: list[str] = []
        ggg2014_proffast_10_outputs: list[str] = []
        ggg2014_proffast_22_outputs: list[str] = []
        ggg2014_proffast_23_outputs: list[str] = []
        ggg2014_proffast_24_outputs: list[str] = []
        ggg2020_proffast_22_outputs: list[str] = []
        ggg2020_proffast_23_outputs: list[str] = []
        ggg2020_proffast_24_outputs: list[str] = []
        console.print(f"determining sensor data contexts for sensor {sensor.sensor_id}")
        sdcs = em27_metadata_interface.get(
            sensor_id=sensor.sensor_id,
            from_datetime=sensor.setups[0].from_datetime,
            to_datetime=sensor.setups[-1].to_datetime
        )
        with rich.progress.Progress() as progress:
            task = progress.add_task("parsing all sensor data contexts", total=len(sdcs))
            for sdc in sdcs:
                dates = tum_esm_utils.timing.date_range(
                    sdc.from_datetime.date(), sdc.to_datetime.date()
                )
                subtask = progress.add_task(
                    f"{sdc.from_datetime.date()} - {sdc.to_datetime.date()} ({sdc.location.location_id})",
                    total=len(dates)
                )
                for date in dates:
                    from_datetimes.append(
                        max(
                            datetime.datetime.combine(
                                date, datetime.time.min, tzinfo=datetime.timezone.utc
                            ), sdc.from_datetime
                        )
                    )
                    to_datetimes.append(
                        min(
                            datetime.datetime.combine(
                                date, datetime.time.max, tzinfo=datetime.timezone.utc
                            ), sdc.to_datetime
                        )
                    )
                    location_ids.append(sdc.location.location_id)
                    interferograms.append(
                        _count_ifg_datapoints(
                            config.general.data.interferograms.root,
                            sensor.sensor_id,
                            date,
                        )
                    )
                    ground_pressure.append(
                        _count_ground_pressure_datapoints(
                            config,
                            sensor.sensor_id,
                            date,
                        )
                    )
                    ggg2014_profiles.append(
                        _ggg2014_profiles_exists(
                            config.general.data.atmospheric_profiles.root,
                            sdc.location.lat,
                            sdc.location.lon,
                            date,
                        )
                    )
                    ggg2020_profiles.append(
                        _ggg2020_profiles_exists(
                            config.general.data.atmospheric_profiles.root,
                            sdc.location.lat,
                            sdc.location.lon,
                            date,
                        )
                    )
                    ggg2014_proffast_10_outputs.append(
                        _check_retrieval_output(config, date, sdc, "proffast-1.0", "GGG2014")
                    )
                    ggg2014_proffast_22_outputs.append(
                        _check_retrieval_output(config, date, sdc, "proffast-2.2", "GGG2014")
                    )
                    ggg2014_proffast_23_outputs.append(
                        _check_retrieval_output(config, date, sdc, "proffast-2.3", "GGG2014")
                    )
                    ggg2014_proffast_24_outputs.append(
                        _check_retrieval_output(config, date, sdc, "proffast-2.4", "GGG2014")
                    )
                    ggg2020_proffast_22_outputs.append(
                        _check_retrieval_output(config, date, sdc, "proffast-2.2", "GGG2020")
                    )
                    ggg2020_proffast_23_outputs.append(
                        _check_retrieval_output(config, date, sdc, "proffast-2.3", "GGG2020")
                    )
                    ggg2020_proffast_24_outputs.append(
                        _check_retrieval_output(config, date, sdc, "proffast-2.4", "GGG2020")
                    )
                    progress.advance(subtask)
                progress.remove_task(subtask)
                progress.advance(task)

        df = pl.DataFrame({
            "from_datetime": from_datetimes,
            "to_datetime": to_datetimes,
            "location_id": location_ids,
            "interferograms": interferograms,
            "ground_pressure": ground_pressure,
            "ggg2014_profiles": ggg2014_profiles,
            "ggg2014_proffast_10_outputs": ggg2014_proffast_10_outputs,
            "ggg2014_proffast_22_outputs": ggg2014_proffast_22_outputs,
            "ggg2014_proffast_23_outputs": ggg2014_proffast_23_outputs,
            "ggg2014_proffast_24_outputs": ggg2014_proffast_24_outputs,
            "ggg2020_profiles": ggg2020_profiles,
            "ggg2020_proffast_22_outputs": ggg2020_proffast_22_outputs,
            "ggg2020_proffast_23_outputs": ggg2020_proffast_23_outputs,
            "ggg2020_proffast_24_outputs": ggg2020_proffast_24_outputs,
        }).with_columns([
            pl.col("location_id").str.pad_start(8),
            pl.col("interferograms").cast(str).str.pad_start(5),
            pl.col("ground_pressure").cast(str).str.pad_start(5),
        ])
        df.write_csv(
            tum_esm_utils.files.rel_to_abs_path(f"../../data/reports/{sensor.sensor_id}.csv"),
            datetime_format="%Y-%m-%dT%H:%M:%S%z",
        )
        console.print(
            f"exported report for sensor {sensor.sensor_id} " +
            f"to data/reports/{sensor.sensor_id}.csv"
        )
