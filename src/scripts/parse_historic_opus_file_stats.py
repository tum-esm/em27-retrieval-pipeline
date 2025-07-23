import sys
from typing import Optional
import datetime
import os
import tqdm
import tum_esm_utils
import sys

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../.."))

from src import utils

# TODO: set these paths
IFG_PATH = tum_esm_utils.files.rel_to_abs_path("../../data/testing/inputs/data/interferograms")
RESULTS_PATH = tum_esm_utils.files.rel_to_abs_path("../../data/testing/inputs/results")

if __name__ == "__main__":
    # call as "s.py allowedsid1 allowedsid2 ..."
    allowed_sensor_ids: Optional[set[str]] = None
    if len(sys.argv) > 1:
        allowed_sensor_ids = set(sys.argv[1:])

    if not os.path.exists(IFG_PATH):
        raise FileNotFoundError(f"IFG_PATH does not exist: {IFG_PATH}")
    if not os.path.exists(RESULTS_PATH):
        raise FileNotFoundError(f"RESULTS_PATH does not exist: {RESULTS_PATH}")

    retrieval_algorithms = set(
        ["proffast-1.0", "proffast-2.2", "proffast-2.3", "proffast-2.4", "proffast-2.4.1"]
    ).intersection(set(os.listdir(RESULTS_PATH)))

    for retrieval_algorithm in retrieval_algorithms:
        for atmospheric_profile_model in ["GGG2014", "GGG2020"]:
            d1 = os.path.join(RESULTS_PATH, retrieval_algorithm, atmospheric_profile_model)
            if not os.path.isdir(d1):
                continue
            for sensor_id in sorted(os.listdir(d1)):
                if (allowed_sensor_ids is not None) and (sensor_id not in allowed_sensor_ids):
                    continue
                d2 = os.path.join(d1, sensor_id, "successful")
                if not os.path.isdir(d2):
                    continue
                print(f"Processing results in {d2}")

                progress = tqdm.tqdm(sorted(os.listdir(d2), reverse=True))
                for results_dir in progress:
                    results_path = os.path.join(d2, results_dir)
                    if not os.path.isdir(results_path):
                        continue

                    progress.set_description(f"{results_dir}")
                    if os.path.exists(os.path.join(results_path, "opus_file_stats.csv")):
                        continue

                    about = tum_esm_utils.files.load_json_file(
                        os.path.join(results_path, "about.json")
                    )
                    try:
                        ifg_file_regex = about["config"]["retrieval"]["general"]["ifg_file_regex"]
                    except KeyError:
                        progress.write(
                            f"Skipping {results_dir} because 'ifg_file_regex' is not defined in 'about.json'."
                        )
                        continue

                    date_string = results_dir[:8]
                    ifg_dir = os.path.join(IFG_PATH, sensor_id, date_string)
                    date = datetime.datetime.strptime(date_string, "%Y%m%d").date()
                    try:
                        opus_filenames = os.listdir(ifg_dir)
                    except FileNotFoundError:
                        progress.write(
                            f"Skipping {results_dir} because the ifg dir does not exists ({ifg_dir})."
                        )
                        continue

                    filtered_filenames = sorted(
                        [
                            f
                            for f in opus_filenames
                            if utils.text.replace_regex_placeholders(
                                ifg_file_regex, sensor_id, date
                            )[1].match(f)
                            is not None
                        ]
                    )

                    # find preprocess input file to get the used filenames
                    input_filenames: list[str]
                    if retrieval_algorithm == "proffast-1.0":
                        input_filenames = (
                            tum_esm_utils.files.load_file(
                                os.path.join(results_path, "logfiles/preprocess4.log")
                            )
                            .split("Reading file names")[1]
                            .split("Done!")[0]
                            .strip(" \t\n")
                        ).split("\n")
                    else:
                        # find preprocess input file to get the used filenames
                        input_file_dir = os.path.join(results_path, "input_files")
                        input_files = [
                            f
                            for f in os.listdir(input_file_dir)
                            if f.startswith("preprocess") and f.endswith(".inp")
                        ]
                        if len(input_files) != 1:
                            progress.write(
                                f"Skipping {results_dir} because there is not exactly one input file in {input_file_dir}: {input_files}"
                            )
                            continue
                        input_filenames = (
                            tum_esm_utils.files.load_file(
                                os.path.join(input_file_dir, input_files[0])
                            )
                            .split("$")[-1]
                            .strip(" *\n\t")
                        ).split("\n")

                    if len(input_filenames) > len(filtered_filenames):
                        progress.write(
                            f"Skipping {results_dir} because there are less files now ({len(filtered_filenames)}) than during processing ({len(input_filenames)})."
                        )
                        continue

                    renamed_files: list[str] = []
                    instrument_vars = [
                        "ABP",
                        "LWN",
                        "RSN",
                        "TSC",
                        "DUR",
                        "MVD",
                        "PKA",
                        "PKL",
                        "PRA",
                        "PRL",
                        "P2A",
                        "P2L",
                        "P2R",
                        "P2K",
                    ]
                    file_checksums: list[str] = []
                    instrument_values: list[list[Optional[float]]] = []
                    for ifg_index, filename in enumerate(filtered_filenames):
                        filepath = os.path.join(ifg_dir, filename)
                        renamed_files.append(f"{date_string[2:]}SN.{ifg_index + 1}")
                        file_checksums.append(tum_esm_utils.files.get_file_checksum(filepath))

                        values: list[Optional[float]] = [None] * len(instrument_vars)
                        try:
                            opus_file = tum_esm_utils.opus.OpusFile.read(
                                filepath, interferogram_mode="skip"
                            )
                            for i, var in enumerate(instrument_vars):
                                values[i] = opus_file.channel_parameters[0].instrument.get(
                                    var, None
                                )
                        except:
                            pass
                        instrument_values.append(values)

                    # SAVE STATISTICS ABOUT INTERFEROGRAMS

                    opus_files_content = "opus_filename,retrieval_filename,checksum," + ",".join(
                        [f"instrument_{var}" for var in instrument_vars]
                    )
                    for i in range(len(filtered_filenames)):
                        opus_files_content += (
                            f"\n{filtered_filenames[i]},{renamed_files[i]},{file_checksums[i]},"
                        )
                        opus_files_content += ",".join(
                            [str(v) if v is not None else "" for v in instrument_values[i]]
                        )
                    tum_esm_utils.files.dump_file(
                        os.path.join(results_path, "opus_file_stats.csv.tmp"), opus_files_content
                    )
                    os.rename(
                        os.path.join(results_path, "opus_file_stats.csv.tmp"),
                        os.path.join(results_path, "opus_file_stats.csv"),
                    )
