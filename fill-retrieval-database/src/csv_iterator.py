import glob
from typing import List


class CsvIterator:
    files: List[str]

    def __init__(self, locations: List[str]):
        self.locations = locations
        self.files = []

        for location in locations:
            # path = '../{}/comb_invparms_*_SN???_??????-??????.csv'.format(location)
            path = "{}/proffast-?.?-outputs-????????-??.csv".format(location)
            files = glob.glob(path)
            self.files.extend(files)

    def has_next_file(self) -> bool:
        return not self.files

    def read_next_file(self) -> str:
        if self.has_next_file():
            first_elem = self.files[0]
            self.files.remove(first_elem)
            return first_elem
        else:
            raise ValueError("There are no more files")
