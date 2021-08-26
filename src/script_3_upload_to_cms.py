import os
from .helpers.utils import load_json, ls_ext
from .helpers.validator import Validator
from .helpers.firestore import Firestore
from rich.progress import track

data_dir = os.path.join(os.path.dirname(__file__), "../data")


def run():
    """
    Upload the files in the local directories `data/json-out`
    and `data/meta-out` to the database.
    """

    # Upload all days
    for day_json_file in track(
        ls_ext(f"{data_dir}/json-out", ".json"), description="Upload to Firestore"
    ):
        Firestore.set_day(load_json(f"{data_dir}/json-out/{day_json_file}"))

    # Fetch and validate local meta
    Firestore.set_meta(load_json(f"{data_dir}/meta-out/meta.json"))
