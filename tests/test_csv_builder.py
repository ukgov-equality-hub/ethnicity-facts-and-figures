import pytest
import json
from flask import url_for

from application.cms.data_utils import TableObjectDownloadBuilder


def test_table_object_builder_does_return_object(stub_simple_table_object):
    builder = TableObjectDownloadBuilder()

    data = builder.process(stub_simple_table_object)

    assert data is not None


def test_table_object_builder_does_build_data_from_simple_table():
    pass


def test_table_object_builder_does_build_data_from_grouped_table():
    pass


def test_table_object_builder_does_build_data_for_multiple_columns_from_simple_table():
    pass


def test_table_object_builder_does_build_data_for_multiple_columns_from_grouped_table():
    pass


def test_table_object_builder_does_apply_column_headings_for_simple_table():
    pass


def test_table_object_builder_does_apply_first_column_heading_for_simple_table():
    pass


def test_table_object_builder_does_apply_column_headings_for_grouped_table():
    pass


def test_table_object_builder_does_apply_first_column_heading_for_grouped_table():
    pass
