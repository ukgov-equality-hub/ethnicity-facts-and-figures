from application.data.tables import TableObjectDataBuilder, TableObjectTableBuilder
from application.data.dimensions import DimensionObjectBuilder


def test_table_object_data_builder_does_return_object(stub_simple_table_object):
    builder = TableObjectDataBuilder()

    table = builder.get_data_table(stub_simple_table_object)

    assert table is not None


def test_table_object_data_builder_does_build_headers_from_simple_table(stub_simple_table_object):
    # given - a
    builder = TableObjectDataBuilder()
    table_object = stub_simple_table_object

    # when we process the object
    table = builder.get_data_table(table_object)

    # then the header for the returned table should match the ones from the simple table
    headers = table.pop(0)
    expected_headers = [table_object["category_caption"]] + table_object["columns"]
    assert headers == expected_headers


def test_table_object_data_builder_does_build_headers_from_legacy_simple_table(stub_simple_table_object):
    # given - a table without a category_caption value
    builder = TableObjectDataBuilder()
    table_object = stub_simple_table_object
    table_object.pop("category_caption", None)

    # when we process the object
    table = builder.get_data_table(table_object)

    # then the header for the returned table should match the ones from the simple table
    headers = table.pop(0)
    expected_headers = ["Ethnicity"] + table_object["columns"]
    assert headers == expected_headers


def test_table_object_data_builder_does_build_data_from_simple_table(stub_simple_table_object):
    # given - a table without a category_caption value
    builder = TableObjectDataBuilder()
    table_object = stub_simple_table_object

    # when we process the object
    data = builder.get_data_table(table_object)
    data.pop(0)

    # then the header for the returned table should match the ones from the simple table
    expected_data = [["White", "25.6", "0.256"], ["Other", "16.6", "0.166"]]
    assert data == expected_data


def test_table_object_data_builder_does_build_headers_from_grouped_table(stub_grouped_table_object):
    # given - a grouped table object
    builder = TableObjectDataBuilder()
    table_object = stub_grouped_table_object

    # when we process the object
    table = builder.get_data_table(table_object)

    # then the header for the returned table should match the ones from the simple table
    headers = table.pop(0)
    # ['Sex', 'Custom category caption', 'Value', 'Rate']
    expected_headers = [table_object["group_column"], table_object["category_caption"]] + table_object["columns"]
    assert headers == expected_headers


def test_table_object_data_builder_does_build_headers_from_legacy_grouped_table(stub_grouped_table_object):
    # given - a
    builder = TableObjectDataBuilder()
    table_object = stub_grouped_table_object
    table_object.pop("category_caption", None)

    # when we process the object
    table = builder.get_data_table(table_object)

    # then the header for the returned table should match the ones from the simple table
    headers = table.pop(0)
    # ['Sex', 'Standard Ethnicity', 'Value', 'Rate']
    expected_headers = [table_object["group_column"], table_object["category"]] + table_object["columns"]
    assert headers == expected_headers


def test_table_object_data_builder_does_build_data_from_grouped_table(stub_grouped_table_object):
    # given - a table without a category_caption value
    builder = TableObjectDataBuilder()
    table_object = stub_grouped_table_object

    # when we process the object
    data = builder.get_data_table(table_object)
    data.pop(0)

    # then the header for the returned table should match the ones from the simple table
    expected_data = [
        ["Men", "White", "25.6", "0.256"],
        ["Men", "Other", "16.6", "0.166"],
        ["Women", "White", "12.8", "0.128"],
        ["Women", "Other", "10.0", "0.100"],
    ]
    assert data == expected_data


def test_table_object_table_builder_does_build_headings_from_grouped_table(stub_grouped_table_object):
    # given - a table without a category_caption value
    builder = TableObjectTableBuilder()
    table_object = stub_grouped_table_object
    table_object["category_caption"] = "expected caption"

    # when we process the object as a table
    data = builder.get_data_table(table_object)
    headers = data[0:2]

    # then the header for the returned table should match the ones we would expect from this table
    expected_headers = [["", "Men", "", "Women", ""], ["expected caption", "Value", "Rate", "Value", "Rate"]]
    assert expected_headers == headers


def test_table_object_table_builder_does_build_headings_from_grouped_table_without_caption(stub_grouped_table_object):
    # given - a table without a category_caption value
    builder = TableObjectTableBuilder()
    table_object = stub_grouped_table_object
    table_object.pop("category_caption")

    # when we process the object as a table
    data = builder.get_data_table(table_object)
    headers = data[0:2]

    # then the header for the returned table should match the ones we would expect from this tabl
    expected_caption = table_object["category"]
    expected_headers = [["", "Men", "", "Women", ""], [expected_caption, "Value", "Rate", "Value", "Rate"]]
    assert expected_headers == headers


def test_table_object_table_builder_does_build_categories_as_row_captions(stub_grouped_table_object):
    # given - a table without a category_caption value
    builder = TableObjectTableBuilder()
    table_object = stub_grouped_table_object
    table_object.pop("category_caption")

    # when we process the object as a table
    data = builder.get_data_table(table_object)
    data.pop(0)
    data.pop(0)
    categories = [row[0] for row in data]

    # then the header for the returned table should match the ones we would expect from this tabl
    expected_categories = ["White", "Other"]
    assert expected_categories == categories


def test_table_object_table_builder_does_build_data_for_rows(stub_grouped_table_object):
    # given - a table without a category_caption value
    builder = TableObjectTableBuilder()
    table_object = stub_grouped_table_object
    table_object.pop("category_caption")

    # when we process the object as a table
    data = builder.get_data_table(table_object)
    data.pop(0)
    data.pop(0)

    # then the header for the returned table should match the ones we would expect from this tabl
    expected_rows = [["White", "25.6", "0.256", "12.8", "0.128"], ["Other", "16.6", "0.166", "10.0", "0.100"]]
    assert expected_rows == data


def test_table_object_builder_does_build_object_from_simple_table(stub_page_with_simple_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_simple_table.dimensions[0]

    # when we process the object
    table_object = builder.build(dimension)

    # then the header for the returned table should match the ones from the simple table
    assert table_object is not None


def test_table_object_builder_does_build_object_from_grouped_table(stub_page_with_grouped_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_grouped_table.dimensions[0]

    # when we process the object
    table_object = builder.build(dimension)

    # then the header for the returned table should match the ones from the simple table
    assert table_object is not None


def test_table_object_builder_does_build_with_page_level_data_from_simple_table(stub_page_with_simple_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_simple_table.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the measure level info should be brought through
    assert dimension_object["context"]["measure"] == "Test Measure Page"
    assert dimension_object["context"]["measure_guid"] == "test-measure-page"
    assert dimension_object["context"]["measure_slug"] == "test-measure-page"
    assert dimension_object["context"]["location"] == "England"
    assert dimension_object["context"]["title"] == "DWP Stats"
    assert dimension_object["context"]["source_url"] == "http://dwp.gov.uk"
    assert dimension_object["context"]["publisher"] == "Department for Work and Pensions"


def test_dimension_object_builder_does_build_with_page_level_data_from_grouped_table(stub_page_with_grouped_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_grouped_table.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the measure level info should be brought through
    assert dimension_object["context"]["measure"] == "Test Measure Page"
    assert dimension_object["context"]["measure_guid"] == "test-measure-page"
    assert dimension_object["context"]["measure_slug"] == "test-measure-page"
    assert dimension_object["context"]["location"] == "England"
    assert dimension_object["context"]["title"] == "DWP Stats"
    assert dimension_object["context"]["source_url"] == "http://dwp.gov.uk"
    assert dimension_object["context"]["publisher"] == "Department for Work and Pensions"


def test_table_object_builder_does_build_with_dimension_level_data_from_simple_table(stub_page_with_simple_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_simple_table.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the dimension level info should be brought through
    assert dimension_object["context"]["dimension"] == "stub dimension"
    assert dimension_object["context"]["guid"] == "stub_dimension"
    assert dimension_object["context"]["time_period"] == "stub_timeperiod"


def test_table_object_builder_does_build_with_dimension_level_data_from_grouped_table(stub_page_with_grouped_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_grouped_table.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the dimension level info should be brought through
    assert dimension_object["context"]["dimension"] == "stub dimension"
    assert dimension_object["context"]["guid"] == "stub_dimension"
    assert dimension_object["context"]["time_period"] == "stub_timeperiod"
