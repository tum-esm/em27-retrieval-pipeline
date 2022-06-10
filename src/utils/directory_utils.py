import subprocess


def directories_are_equal(_dir1: str, _dir2: str):
    return (
        len(
            subprocess.run(
                ["diff", "--brief", "--recursive", _dir1, _dir2], capture_output=True
            )
            .stdout.decode()
            .split("\n")
        )
        == 1
    )


def get_existing_src_directories(config: dict, sensor: str, date: int):
    SRC_DIRECTORIES = [
        [config["src"]["interferograms"]["upload"][sensor]],
        *config["src"]["interferograms"]["other"][sensor],
        [config["dst"] + f"/{sensor}/ifgs"],
    ]

    src_directories = [f"{x}/{date}" for x in SRC_DIRECTORIES]
    existing_src_directories = [x for x in src_directories if os.path.isdir(x)]

    return existing_src_directories


def assert_directory_list_equality(directory_list):
    for i in range(len(directory_list) - 1):
        a = directory_list[i]
        b = directory_list[i + 1]
        assert directories_are_equal(a, b), f"Directories {a} and {b} exist but differ"
