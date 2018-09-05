class EthnicityDataset:
    DEFAULT_ETHNICITY_TYPE_COLUMNS = ["ethnicity type", "ethnicity_type", "ethnicity-type"]

    def __init__(self, data):
        self.data = data
        self.ethnicity_index = self.__get_ethnicity_index()
        self.ethnicity_type_index = self.__get_ethnicity_type_index()

    def __len__(self):
        return len(self.data) - 1

    def __get_ethnicity_index(self):
        simple_headers = [header.strip().lower() for header in self.get_headers()]
        for index, cell in enumerate(simple_headers):
            if cell.startswith("ethnic"):
                return index
        return 0

    def __get_ethnicity_type_index(self):
        simple_headers = [header.strip().lower() for header in self.get_headers()]
        for index, cell in enumerate(simple_headers):
            if cell in self.DEFAULT_ETHNICITY_TYPE_COLUMNS:
                return index
        return self.ethnicity_index

    def get_headers(self):
        return self.data[0]

    def get_ethnicity(self, row):
        return self.data[row + 1][self.ethnicity_index]

    def get_ethnicity_type(self, row):
        return self.data[row + 1][self.ethnicity_type_index]

    def get_data(self):
        return self.data

    def append_headers(self, values):
        self.data[0] += values

    def append_to_row(self, row, values):
        self.data[row + 1] += values
