import datetime
import os
import pytest
import tempfile
from src.retrieval.utils.pressure_loading import find_pressure_files


def _popuplate_directory_structure(root_dir: str, files: dict[str, set[str]]) -> None:
    for subdir, filenames in files.items():
        os.makedirs(os.path.join(root_dir, subdir), exist_ok=True)
        for filename in filenames:
            with open(os.path.join(root_dir, subdir, filename), "w") as f:
                f.write("")


@pytest.mark.order(3)
@pytest.mark.quick
def test_pressure_file_locating() -> None:
    # for a bunch of regexes, test if the correct files are found
    with tempfile.TemporaryDirectory() as tmpdir:
        files = {
            "ma":
                set([
                    "gp-ma-2022-06-02-a.csv",
                    "gp-ma-2022-06-02-b.csv",
                    "gp-ma-2022-06-03.csv",
                    "gp-ma-2022-06-04.csv",
                    "gp-mf-2022-06-04.csv",
                    "gp-2022-06-05.csv",
                    "gp-20220606.csv",
                ]),
            "mf":
                set([
                    "gp-mf-2022-06-02-a.csv",
                    "gp-mf-2022-06-02-a.csv",
                    "gp-2022-06-03-d.csv",
                    "gp-2022-06-04-d.csv",
                ]),
        }
        _popuplate_directory_structure(tmpdir, files)

        print(os.listdir(tmpdir))

        # QUERY 1

        r1 = find_pressure_files(
            tmpdir, "ma", r"gp-$(SENSOR_ID)-$(YYYY)-$(MM)-$(DD)\.csv", datetime.date(2022, 6, 3)
        )
        assert set(r1[0]) == files["ma"]
        assert set(r1[1]) == set([
            "gp-ma-2022-06-03.csv",
            "gp-ma-2022-06-04.csv",
        ])
        assert set(r1[2]) == set(["gp-ma-2022-06-03.csv"])

        # QUERY 2

        r2 = find_pressure_files(
            tmpdir, "ma", r"gp-$(SENSOR_ID)-$(YYYY)-$(MM)-$(DD).*\.csv", datetime.date(2022, 6, 2)
        )
        assert set(r2[0]) == files["ma"]
        assert set(r2[1]) == set([
            "gp-ma-2022-06-02-a.csv",
            "gp-ma-2022-06-02-b.csv",
            "gp-ma-2022-06-03.csv",
            "gp-ma-2022-06-04.csv",
        ])
        assert set(r2[2]) == set([
            "gp-ma-2022-06-02-a.csv",
            "gp-ma-2022-06-02-b.csv",
        ])

        # QUERY 3

        r3 = find_pressure_files(
            tmpdir, "ma", r".*-$(YYYY)-$(MM).*\.csv", datetime.date(2022, 6, 20)
        )
        assert set(r3[0]) == files["ma"]
        assert set(r3[1]) == set([
            "gp-ma-2022-06-02-a.csv",
            "gp-ma-2022-06-02-b.csv",
            "gp-ma-2022-06-03.csv",
            "gp-ma-2022-06-04.csv",
            "gp-mf-2022-06-04.csv",
            "gp-2022-06-05.csv",
        ])
        assert set(r3[2]) == set([
            "gp-ma-2022-06-02-a.csv",
            "gp-ma-2022-06-02-b.csv",
            "gp-ma-2022-06-03.csv",
            "gp-ma-2022-06-04.csv",
            "gp-mf-2022-06-04.csv",
            "gp-2022-06-05.csv",
        ])

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


