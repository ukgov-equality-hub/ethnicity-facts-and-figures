import os

from application.utils import get_csv_data_for_download


def test_adds_quotes():
    directory = os.path.abspath(os.path.dirname(__file__))
    csv_with_no_quotes = os.path.join(directory, "test_data/csv_with_no_quotes.csv")

    csv_with_quotes = '"Ethnicity","Value"\n"Black","10"\n"White","12.2"\n'

    assert get_csv_data_for_download(csv_with_no_quotes) == csv_with_quotes
