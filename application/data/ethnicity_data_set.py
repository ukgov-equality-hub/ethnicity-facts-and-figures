from typing import List
from typing import Union


class EthnicityDataset:
    DEFAULT_ETHNICITY_TYPE_COLUMNS = ["ethnicity type", "ethnicity_type", "ethnicity-type"]

    def __init__(self, data: List[List[str]]) -> None:
        self.data = data
        self.ethnicity_index = self.__get_ethnicity_index()
        self.ethnicity_type_index = self.__get_ethnicity_type_index()

    def __len__(self) -> int:
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

    def get_headers(self) -> List[str]:
        return self.data[0]

    def get_ethnicity(self, row: int) -> str:
        return self.data[row + 1][self.ethnicity_index]

    def get_ethnicity_type(self, row: int) -> str:
        return self.data[row + 1][self.ethnicity_type_index]

    def get_data(self) -> List[List[str]]:
        return self.data

    def get_unique_ethnicities(self):
        return {row[self.ethnicity_index] for row in self.data}

    def append_headers(self, values: List[str]) -> None:
        self.data[0] += values

    def append_to_row(self, row: int, values: Union[List[Union[int, str]], List[str]]) -> None:
        self.data[row + 1] += values
