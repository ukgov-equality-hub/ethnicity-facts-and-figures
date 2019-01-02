from application.utils import get_csv_data_for_download


def test_adds_quotes():
    csv_with_no_quotes = "./tests/test_data/csv_with_no_quotes.csv"

    csv_with_quotes = '"Ethnicity","Value"\n"Black","10"\n"White","12.2"\n'

    assert get_csv_data_for_download(csv_with_no_quotes) == csv_with_quotes


def test_only_adds_quotes_to_non_quoted_values():
    csv_with_embedded_quotes = "./tests/test_data/csv_with_embedded_quotes.csv"

    csv_with_quotes = '"Ethnicity","Value","Description"\n"Black","10","Test"\n"White","12.2","This is a ""test"""\n'

    assert get_csv_data_for_download(csv_with_embedded_quotes) == csv_with_quotes
