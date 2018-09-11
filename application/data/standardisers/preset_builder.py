from application.data.standardisers.ethnicity_classification_finder import (
    EthnicityStandardiser,
    EthnicityClassificationCollection,
    EthnicityClassification,
    EthnicityClassificationDataItem,
    EthnicityClassificationFinder,
)
from application.utils import get_bool


class EthnicityClassificationFileColumn:
    """
    An enum that defines columns when loading an EthnicityClassificationFinder from a settings file
    """

    CODE = 0
    NAME = 1
    STANDARD_VALUE = 2
    DISPLAY_VALUE = 3
    PARENT = 4
    ORDER = 5
    REQUIRED = 6


class EthnicityClassificationDataColumn:
    """
    An enum that defines columns when loading an EthnicityClassification from data (i.e. a list of lists)
    """

    STANDARD_VALUE = 0
    DISPLAY_VALUE = 1
    PARENT = 2
    ORDER = 3
    REQUIRED = 4


def preset_search_from_file(standardiser_file, preset_collection_file):
    standardiser = standardiser_from_file(standardiser_file)
    preset_collection = preset_collection_from_file(preset_collection_file)

    return EthnicityClassificationFinder(standardiser, preset_collection)


def preset_search_from_data(standardiser_data, preset_collection_data):
    standardiser = standardiser_from_data(standardiser_data)
    preset_collection = preset_collection_from_data(preset_collection_data)

    return EthnicityClassificationFinder(standardiser, preset_collection)


def standardiser_from_file(file_name):
    standardiser_data = __read_data_from_file_no_headers(file_name)

    return standardiser_from_data(standardiser_data)


def standardiser_from_data(standardiser_data):
    standardiser = EthnicityStandardiser()
    for row in standardiser_data:
        standardiser.add_conversion(raw_ethnicity=row[0], standard_ethnicity=row[1])

    return standardiser


def preset_collection_from_file(file_name):
    preset_file_data = __read_data_from_file_no_headers(file_name)

    return preset_collection_from_data(preset_file_data)


def preset_collection_from_data(collection_data):
    preset_codes = set([row[EthnicityClassificationFileColumn.CODE] for row in collection_data])

    preset_collection = EthnicityClassificationCollection()
    for code in preset_codes:
        preset_collection.add_classification(__preset_from_complete_data(code, collection_data))
    return preset_collection


def preset_collection_from_preset_list(presets):
    preset_collection = EthnicityClassificationCollection()
    for preset in presets:
        preset_collection.add_classification(preset)
    return preset_collection


def preset_from_data(code, name, data_rows):
    preset = EthnicityClassification(code=code, name=name)
    for row in data_rows:
        standard_value = row[EthnicityClassificationDataColumn.STANDARD_VALUE]
        preset_item = __preset_data_item_from_data(row)
        preset.add_data_item_to_classification(standard_value, preset_item)
    return preset


def __preset_data_item_from_data(data_row):
    item_is_required = get_bool(data_row[EthnicityClassificationDataColumn.REQUIRED])
    return EthnicityClassificationDataItem(
        display_ethnicity=data_row[EthnicityClassificationDataColumn.DISPLAY_VALUE],
        parent=data_row[EthnicityClassificationDataColumn.PARENT],
        order=data_row[EthnicityClassificationDataColumn.ORDER],
        required=item_is_required,
    )


def __preset_from_complete_data(preset_code, complete_data):
    this_preset_data = [row for row in complete_data if row[EthnicityClassificationFileColumn.CODE] == preset_code]

    preset = EthnicityClassification(
        code=this_preset_data[0][EthnicityClassificationFileColumn.CODE], name=this_preset_data[0][EthnicityClassificationFileColumn.NAME]
    )
    for row in this_preset_data:
        data_item = __preset_data_item_from_file_data_row(row)
        preset.add_data_item_to_classification(row[EthnicityClassificationFileColumn.STANDARD_VALUE], data_item)
    return preset


def __preset_data_item_from_file_data_row(file_row):
    item_is_required = get_bool(file_row[EthnicityClassificationFileColumn.REQUIRED])
    return EthnicityClassificationDataItem(
        display_ethnicity=file_row[EthnicityClassificationFileColumn.DISPLAY_VALUE],
        parent=file_row[EthnicityClassificationFileColumn.PARENT],
        order=file_row[EthnicityClassificationFileColumn.ORDER],
        required=item_is_required,
    )


def __read_data_from_file_no_headers(file_name):
    import csv

    with open(file_name, "r") as f:
        reader = csv.reader(f)
        data = list(reader)
        if len(data) > 1:
            return data[1:]
    return []
