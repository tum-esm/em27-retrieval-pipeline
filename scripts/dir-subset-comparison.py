import os
import subprocess
import sys


def print_directory_comparison(dir_a: str, dir_b: str) -> None:
    process_a = subprocess.run(["du", "-d", "0", dir_a], capture_output=True)
    process_b = subprocess.run(["du", "-d", "0", dir_b], capture_output=True)

    size_of_a = process_a.stdout.decode().replace(dir_a, "").strip()
    size_of_b = process_b.stdout.decode().replace(dir_b, "").strip()

    set_a = set(os.listdir(dir_a))
    set_b = set(os.listdir(dir_b))
    only_in_a: list[str] = set_a.difference(set_b)
    only_in_b: list[str] = set_b.difference(set_a)

    print(f"a: {dir_a}")
    print(f"b: {dir_b}")
    print(f"size of a: {size_of_a}")
    print(f"size of b: {size_of_b}")
    print(
        f"only in a: {list(only_in_a) if len(only_in_a) < 5 else f'{len(only_in_a)} items'}"
    )
    print(
        f"only in b: {list(only_in_b) if len(only_in_b) < 5 else f'{len(only_in_b)} items'}"
    )


if __name__ == "__main__":
    try:
        assert len(sys.argv) == 3
        assert os.path.isdir(sys.argv[1])
        assert os.path.isdir(sys.argv[2])
    except AssertionError:
        raise AssertionError(
            'Please call this with "python dir-subset-comparison.py dirA dirB"'
        )
    print_directory_comparison(sys.argv[1], sys.argv[2])
