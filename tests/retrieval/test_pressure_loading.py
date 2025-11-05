import datetime
import os
import random
from typing import Any
import pytest
import tempfile
import polars as pl
import tum_esm_utils
from src import types
from src.retrieval.utils.pressure_loading import find_pressure_files, load_pressure_file


def _popuplate_directory_structure(root_dir: str, files: dict[str, set[str]]) -> None:
    for subdir, filenames in files.items():
        os.makedirs(os.path.join(root_dir, subdir), exist_ok=True)
        for filename in filenames:
            with open(os.path.join(root_dir, subdir, filename), "w") as f:
                f.write("")


@pytest.mark.order(3)
@pytest.mark.quick
def test_pressure_file_locating() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        files = {
            "ma": set(
                [
                    "gp-ma-2022-06-02-a.csv",
                    "gp-ma-2022-06-02-b.csv",
                    "gp-ma-2022-06-03.csv",
                    "gp-ma-2022-06-04.csv",
                    "gp-mf-2022-06-04.csv",
                    "gp-2022-06-05.csv",
                    "gp-20220606.csv",
                ]
            ),
            "mf": set(
                [
                    "gp-mf-2022-06-02-a.csv",
                    "gp-mf-2022-06-02-a.csv",
                    "gp-2022-06-03-d.csv",
                    "gp-2022-06-04-d.csv",
                ]
            ),
        }
        _popuplate_directory_structure(tmpdir, files)

        # print(os.listdir(tmpdir))

        # QUERY 1

        r1 = find_pressure_files(
            tmpdir, "ma", r"gp-$(SENSOR_ID)-$(YYYY)-$(MM)-$(DD)\.csv", datetime.date(2022, 6, 3)
        )
        assert set(r1[0]) == files["ma"]
        assert set(r1[1]) == set(
            [
                "gp-ma-2022-06-03.csv",
                "gp-ma-2022-06-04.csv",
            ]
        )
        assert set(r1[2]) == set(["gp-ma-2022-06-03.csv"])

        # QUERY 2

        r2 = find_pressure_files(
            tmpdir, "ma", r"gp-$(SENSOR_ID)-$(YYYY)-$(MM)-$(DD).*\.csv", datetime.date(2022, 6, 2)
        )
        assert set(r2[0]) == files["ma"]
        assert set(r2[1]) == set(
            [
                "gp-ma-2022-06-02-a.csv",
                "gp-ma-2022-06-02-b.csv",
                "gp-ma-2022-06-03.csv",
                "gp-ma-2022-06-04.csv",
            ]
        )
        assert set(r2[2]) == set(
            [
                "gp-ma-2022-06-02-a.csv",
                "gp-ma-2022-06-02-b.csv",
            ]
        )

        # QUERY 3

        r3 = find_pressure_files(
            tmpdir, "ma", r".*-$(YYYY)-$(MM).*\.csv", datetime.date(2022, 6, 20)
        )
        assert set(r3[0]) == files["ma"]
        assert set(r3[1]) == set(
            [
                "gp-ma-2022-06-02-a.csv",
                "gp-ma-2022-06-02-b.csv",
                "gp-ma-2022-06-03.csv",
                "gp-ma-2022-06-04.csv",
                "gp-mf-2022-06-04.csv",
                "gp-2022-06-05.csv",
            ]
        )
        assert set(r3[2]) == set(
            [
                "gp-ma-2022-06-02-a.csv",
                "gp-ma-2022-06-02-b.csv",
                "gp-ma-2022-06-03.csv",
                "gp-ma-2022-06-04.csv",
                "gp-mf-2022-06-04.csv",
                "gp-2022-06-05.csv",
            ]
        )

        # QUERY 4

        r4 = find_pressure_files(tmpdir, "mf", r".*$(YYYY).*\.csv", datetime.date(2023, 6, 20))
        assert set(r4[0]) == files["mf"]
        assert set(r4[1]) == files["mf"]
        assert set(r4[2]) == set()

        # QUERY 5

        r5 = find_pressure_files(tmpdir, "mf", r".*\.dat", datetime.date(2022, 6, 2))
        assert set(r5[0]) == files["mf"]
        assert len(r5[1]) == 0
        assert len(r5[2]) == 0

        # QUERY 6

        r6 = find_pressure_files(tmpdir, "mn", r".*", datetime.date(2022, 6, 2))
        assert len(r6[0]) == 0
        assert len(r6[1]) == 0
        assert len(r6[2]) == 0


@pytest.mark.order(3)
@pytest.mark.quick
def test_pressure_file_loading() -> None:
    # for each combination test variants:
    #   all filled, some pressures missing, some dates missing, some times missing

    # test different naming formats for given: utc-date and utc-time

    # test different naming formats for given: utc-datetime

    # test different naming formats for given: unix-timestamp

    # test different naming formats for given: invalid combinations

    with tempfile.TemporaryDirectory() as tmpdir:
        for _ in range(50):
            non_null_count = random.randint(10, 50)
            null_count = random.randint(0, 5)

            random_date = datetime.date(
                random.randint(2010, 2023),
                random.randint(1, 12),
                random.randint(1, 28),
            )

            random_times: list[datetime.time] = []
            while len(random_times) < (non_null_count + null_count):
                t = datetime.time(
                    random.randint(0, 23),
                    random.randint(0, 59),
                    random.randint(0, 59),
                )
                if t not in random_times:
                    random_times.append(t)

            random_pressures = [random.uniform(950, 1050) for _ in range(non_null_count)] + (
                [None] * null_count
            )
            random.shuffle(random_pressures)

            date_column = [random_date.strftime("%Y-%m-%d")] * (non_null_count + null_count)
            time_column = [t.strftime("%H:%M:%S") for t in random_times]
            datetime_column = [f"{date_column[0]}T{t}" for t in time_column]
            timestamp_column = [
                str(int(datetime.datetime.combine(random_date, t).timestamp()))
                for t in random_times
            ]
            pressure_column = [(f"{p:.6f}" if (p is not None) else "") for p in random_pressures]

            for _ in range(10):
                date_column_name = "date" + "".join(
                    random.choices("abcdefghijklmnopqrstuvwxyz", k=5)
                )
                time_column_name = "time" + "".join(
                    random.choices("abcdefghijklmnopqrstuvwxyz", k=5)
                )
                datetime_column_name = "datetime" + "".join(
                    random.choices("abcdefghijklmnopqrstuvwxyz", k=5)
                )
                timestamp_column_name = "timestamp" + "".join(
                    random.choices("abcdefghijklmnopqrstuvwxyz", k=5)
                )
                pressure_column_name = "pressure" + "".join(
                    random.choices("abcdefghijklmnopqrstuvwxyz", k=5)
                )

                base_config: Any = {
                    "path": tum_esm_utils.validators.StrictDirectoryPath(tmpdir),
                    "file_regex": ".*",
                    "separator": ",",
                    "pressure_column": pressure_column_name,
                    "pressure_column_format": "hPa",
                }

                # 1. given date and time

                c1 = types.config.GroundPressureConfig(
                    **base_config,
                    date_column=date_column_name,
                    date_column_format="%Y-%m-%d",
                    time_column=time_column_name,
                    time_column_format="%H:%M:%S",
                )
                with open(os.path.join(tmpdir, "test1.csv"), "w") as f:
                    f.write(
                        f"{date_column_name},{time_column_name},{pressure_column_name}\n"
                        + "\n".join(
                            f"{d},{t},{p}"
                            for d, t, p in zip(date_column, time_column, pressure_column)
                        )
                    )

                # 2. given datetime

                c2 = types.config.GroundPressureConfig(
                    **base_config,
                    datetime_column=datetime_column_name,
                    datetime_column_format="%Y-%m-%dT%H:%M:%S",
                )
                with open(os.path.join(tmpdir, "test2.csv"), "w") as f:
                    f.write(
                        f"{datetime_column_name},{pressure_column_name}\n"
                        + "\n".join(f"{dt},{p}" for dt, p in zip(datetime_column, pressure_column))
                    )

                # 3. given timestamp

                c3 = types.config.GroundPressureConfig(
                    **base_config,
                    unix_timestamp_column=timestamp_column_name,
                    unix_timestamp_column_format="s",
                )
                with open(os.path.join(tmpdir, "test3.csv"), "w") as f:
                    f.write(
                        f"{timestamp_column_name},{pressure_column_name}\n"
                        + "\n".join(f"{ts},{p}" for ts, p in zip(timestamp_column, pressure_column))
                    )

                # print("TEST FILE 1")
                # os.system(f"cat {os.path.join(tmpdir, 'test1.csv')}")
                # print("TEST FILE 2")
                # os.system(f"cat {os.path.join(tmpdir, 'test1.csv')}")
                # print("TEST FILE 3")
                # os.system(f"cat {os.path.join(tmpdir, 'test1.csv')}")

                df1 = load_pressure_file(c1, os.path.join(tmpdir, "test1.csv"))
                df2 = load_pressure_file(c2, os.path.join(tmpdir, "test2.csv"))
                df3 = load_pressure_file(c3, os.path.join(tmpdir, "test3.csv"))

                expected = [
                    e
                    for e in sorted(
                        zip(
                            [
                                datetime.datetime.combine(
                                    random_date, t, tzinfo=datetime.timezone.utc
                                )
                                for t in random_times
                            ],
                            random_pressures,
                        ),
                        key=lambda x: x[0],
                    )
                    if e[1] is not None
                ]

                expected_datetimes = [e[0] for e in expected]
                expected_pressures = [e[1] for e in expected]
                assert len(expected_datetimes) == non_null_count
                assert len(expected_pressures) == non_null_count

                def _test_equality(df: pl.DataFrame) -> None:
                    parsed_datetimes = df1["utc"].to_list()
                    parsed_pressures = df1["pressure"].to_list()
                    assert len(parsed_datetimes) == len(expected_datetimes)
                    assert len(parsed_pressures) == len(expected_pressures)
                    for a, b in zip(parsed_datetimes, expected_datetimes):
                        assert a == b
                    for c, d in zip(parsed_pressures, expected_pressures):
                        assert round(c, 6) == round(d, 6)  # type: ignore

                # print("\n\nEXPECTED:")
                # for i in range(non_null_count):
                #     print(f"{expected_datetimes[i]}: {expected_pressures[i]}")

                # print(f"\n\nPARSED 1: {df1}")
                # print(f"\n\nPARSED 2: {df2}")
                # print(f"\n\nPARSED 3: {df3}")

                _test_equality(df1)
                _test_equality(df2)
                _test_equality(df3)
