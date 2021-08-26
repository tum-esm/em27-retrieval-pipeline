import os
from src import script_1_extract_data_from_db, script_2_transform_db_csv

project_dir = "/".join(__file__.split("/")[:-1])


def clear_upload_data():
    for subdir in ["csv-in", "csv-out", "json-out", "meta-out"]:
        d = f"{project_dir}/data/{subdir}"
        filelist = [
            f for f in os.listdir(d) if f.endswith(".json") or f.endswith(".csv")
        ]
        for f in filelist:
            os.remove(f"{d}/{f}")


def run(date):
    # clear_upload_data()
    # script_1_extract_data_from_db.run(date)
    script_2_transform_db_csv.run()


if __name__ == "__main__":
    run(f"20210727")
