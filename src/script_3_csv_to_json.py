import os
import pandas as pd
from .helpers.utils import load_json, ls_ext, dump_json, concat, unique
from .helpers.validator import Validator
from .helpers.firestore import Firestore
from rich.progress import track


data_dir = os.path.join(os.path.dirname(__file__), "../data")


def run(dates: list[str]):
    """
    Convert data in `data/csv-out` to `data/json-out`, which will
    be the json format used by the database. In here, the `meta.json`
    document will also be generated.

    Examples in the README.md.
    """

    # Load and validate local meta
    meta = Firestore.get_meta()
    Validator.meta(meta)

    date_strings = [f"{date[:4]}-{date[4:6]}-{date[6:8]}" for date in dates]
    meta["days"] = [d for d in meta["days"] if d not in date_strings]

    # Loop through all csv files in csv-out
    for day_csv in track(
        ls_ext(f"{data_dir}/csv-out", ".csv"), description="Convert to json"
    ):
        df = pd.read_csv(f"{data_dir}/csv-out/{day_csv}")

        # Add date string to meta.json
        date_string = f"{day_csv[:4]}-{day_csv[4:6]}-{day_csv[6:8]}"
        if date_string not in meta["days"]:
            meta["days"].append(date_string)

        # Generate the json file corresponding to each csv file
        json_object = {
            "date": date_string,
            "timestamps": list(df["timestamp"]),
        }
        for gas in ["co2", "ch4"]:
            json_object[gas] = {}
            for station in ["TUM_I", "TAU", "GRA", "OBE", "FEL"]:
                try:
                    timeseries = list(
                        map(
                            lambda d: 0 if str(d) == "nan" else round(d, 6),
                            df[f"{station}_x{gas}"],
                        )
                    )
                except:
                    timeseries = [0] * len(json_object["timestamps"])
                json_object[gas][station] = timeseries

        dump_json(f"{data_dir}/json-out/{day_csv[:-4]}.json", json_object)

    # Save meta.json
    meta["days"].sort()

    dump_json(f"{data_dir}/meta-out/meta.json", meta)
