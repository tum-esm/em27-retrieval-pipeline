import os
from rich.progress import track
from src import (
    script_1_extract_data_from_db,
    script_2_generate_plot_json,
    script_3_upload_to_cms,
)

project_dir = "/".join(__file__.split("/")[:-1])


def clear_upload_data():
    for subdir in ["csv-in", "json-out"]:
        d = f"{project_dir}/data/{subdir}"
        filelist = [
            f for f in os.listdir(d) if f.endswith(".json") or f.endswith(".csv")
        ]
        for f in filelist:
            os.remove(f"{d}/{f}")


def run(dates):
    clear_upload_data()
    for date in track(dates, description="Extract data from db"):
        script_1_extract_data_from_db.run(date)
    script_2_generate_plot_json.run(minify=True)
    script_3_upload_to_cms.run()


if __name__ == "__main__":
    dates = []
    for month in range(7, 10):
        dates += [
            f"2021{str(month).zfill(2)}{str(day).zfill(2)}" for day in range(1, 32)
        ]

    run(dates)

    # script_1_extract_data_from_db.run("20210812")
    # script_3_upload_to_cms.run()
