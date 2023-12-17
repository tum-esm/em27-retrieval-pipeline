import datetime
import os
from typing import Literal
from rich.console import Console
from rich.table import Table
from rich.rule import Rule
import em27_metadata
from src import types, utils


def generate_new_table() -> Table:
    table = Table()
    table.add_column("date")
    table.add_column("interfe-\nrograms")
    table.add_column("data-\nlogger")
    table.add_column("GGG2014\nprofiles", overflow="fold")
    table.add_column("GGG2014\nprf1.0 out", overflow="fold")
    table.add_column("GGG2014\nprf2.2 out", overflow="fold")
    table.add_column("GGG2014\nprf2.3 out", overflow="fold")
    table.add_column("GGG2020\nprofiles", overflow="fold")
    table.add_column("GGG2020\nprf2.2 out", overflow="fold")
    table.add_column("GGG2020\nprf2.3 out", overflow="fold")
    return table


# date | location id | interferograms | datalogger | profiles | prf1.0 GGG2014 | prf2.2 GGG2014 | prf2.2 GGG2020 | prf2.3 GGG202014 | prf2.3 GGG2020

config = types.Config.load()
metadata = em27_metadata.load_from_github(
    github_repository=config.general.metadata.github_repository,
    access_token=config.general.metadata.access_token,
)


def _date_range(
    from_date: datetime.date,
    to_date: datetime.date,
) -> list[datetime.date]:
    delta = to_date - from_date
    assert delta.days >= 0, "from_date must be before to_date"
    return [
        from_date + datetime.timedelta(days=i) for i in range(delta.days + 1)
    ]


def _ggg2014_profiles_exists(
    path: str,
    lat: float,
    lon: float,
    date: datetime.date,
) -> bool:
    date_string = date.strftime("%Y%m%d")
    coords_string = utils.text.get_coordinates_slug(lat, lon)
    print(os.path.join(path, "GGG2014", f"{date_string}_{coords_string}.map"))
    return os.path.isfile(
        os.path.join(path, "GGG2014", f"{date_string}_{coords_string}.map")
    )


def _ggg2020_profiles_exists(
    path: str,
    lat: float,
    lon: float,
    date: datetime.date,
) -> bool:
    date_string = date.strftime("%Y%m%d")
    coords_string = utils.text.get_coordinates_slug(lat, lon)
    return all([
        os.path.isfile(
            os.path.join(
                path, "GGG2020", f"{date_string}{h:02d}_{coords_string}.map"
            )
        ) for h in range(0, 22, 3)
    ])


def _interferogram_datapoints(
    path: str,
    sensor_id: str,
    date: datetime.date,
) -> int:

    try:
        return len(
            os.listdir(os.path.join(path, sensor_id, date.strftime('%Y%m%d')))
        )
    except FileNotFoundError:
        return 0


def _datalogger_datapoints(
    path: str,
    sensor_id: str,
    date: datetime.date,
) -> int:
    try:
        with open(
            os.path.join(
                path, sensor_id,
                f"datalogger-{sensor_id}-{date.strftime('%Y%m%d')}.csv"
            ), "r"
        ) as f:
            return len(f.readlines()) - 1
    except FileNotFoundError:
        return 0


def convert_stat_to_string(stat: list[int]) -> str:
    if stat[0] == 0 and stat[1] == 0:
        return "-"
    if stat[0] == 0 and stat[2] == 0:
        return "❌"
    if stat[1] == 0 and stat[2] == 0:
        return "✅"
    return f"⏳\n{stat[0]}S,{stat[1]}F,{stat[2]}P"


config = types.Config.load()

for sensor in metadata.sensors[: 1]:
    console = Console(record=True)
    for location in sensor.locations[: 2]:
        l = next(
            filter(
                lambda l: l.location_id == location.location_id,
                metadata.locations
            )
        )
        console.print(
            Rule(
                f"{sensor.sensor_id} - {location.location_id} ({l.lat}, {l.lon})"
                + f" - {location.from_datetime} to {location.to_datetime}"
            )
        )
        table = generate_new_table()
        for date in _date_range(
            location.from_datetime.date(), location.to_datetime.date()
        ):
            out_states: list[Literal["successful", "failed", "missing"]] = []
            _gg2014 = _ggg2014_profiles_exists(
                config.general.data.atmospheric_profiles.root, l.lat, l.lon,
                date
            )
            _gg2020 = _ggg2020_profiles_exists(
                config.general.data.atmospheric_profiles.root, l.lat, l.lon,
                date
            )
            stats = {
                "GGG2014": {
                    "proffast-1.0": [0, 0, 0],
                    "proffast-2.2": [0, 0, 0],
                    "proffast-2.3": [0, 0, 0],
                },
                "GGG2020": {
                    "proffast-2.2": [0, 0, 0],
                    "proffast-2.3": [0, 0, 0],
                },
            }
            for sdc in metadata.get(
                sensor_id=sensor.sensor_id,
                from_datetime=max(
                    datetime.datetime.combine(
                        date, datetime.time.min, tzinfo=datetime.UTC
                    ), location.from_datetime
                ),
                to_datetime=min(
                    datetime.datetime.combine(
                        date, datetime.time.max, tzinfo=datetime.UTC
                    ), location.to_datetime
                ),
            ):
                output_folder_slug = sdc.from_datetime.strftime("%Y%m%d")
                if sdc.multiple_ctx_on_this_date:
                    output_folder_slug += sdc.from_datetime.strftime("_%H%M%S")
                    output_folder_slug += sdc.to_datetime.strftime("_%H%M%S")

                for a in stats.keys():
                    for r in stats[a].keys():
                        success_path = os.path.join(
                            config.general.data.results.root,
                            f"{r}/{a}/{sensor.sensor_id}/successful",
                            output_folder_slug
                        )
                        failed_path = os.path.join(
                            config.general.data.results.root,
                            f"{r}/{a}/{sensor.sensor_id}/failed",
                            output_folder_slug
                        )
                        if os.path.isdir(success_path):
                            stats[a][r][0] += 1
                        elif os.path.isdir(failed_path):
                            stats[a][r][1] += 1
                        else:
                            stats[a][r][2] += 1

            table.add_row(
                str(date),
                str(
                    _interferogram_datapoints(
                        config.general.data.interferograms.root,
                        sensor.sensor_id,
                        date,
                    )
                ),
                str(
                    _datalogger_datapoints(
                        config.general.data.datalogger.root,
                        sensor.sensor_id,
                        date,
                    )
                ),
                "✅" if _gg2014 else "-",
                convert_stat_to_string(stats["GGG2014"]["proffast-1.0"]),
                convert_stat_to_string(stats["GGG2014"]["proffast-2.2"]),
                convert_stat_to_string(stats["GGG2014"]["proffast-2.3"]),
                "✅" if _gg2020 else "-",
                convert_stat_to_string(stats["GGG2020"]["proffast-2.2"]),
                convert_stat_to_string(stats["GGG2020"]["proffast-2.3"]),
            )

        console.print(table)

    with open(f"{sensor.sensor_id}.txt", "w") as f:
        f.write(console.export_text())
