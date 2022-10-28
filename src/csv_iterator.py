import glob


class CsvIterator:

    def __init__(self, locations):
        self.locations = locations
        self.files = []

        for location in locations:
            # path = '../{}/comb_invparms_*_SN???_??????-??????.csv'.format(location)
            path = '{}/proffast-?.?-outputs-????????-??.csv'.format(location)
            files = glob.glob(path)
            self.files.extend(files)

    def has_next_file(self):
        return self.files

    def read_next_file(self):
        if self.has_next_file():
            first_elem = self.files[0]
            self.files.remove(first_elem)
            return first_elem
        else:
            return None
