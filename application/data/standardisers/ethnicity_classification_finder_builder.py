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


def ethnicity_classification_finder_from_file(standardiser_file, classification_collection_file):
    standardiser = ethnicity_standardiser_from_file(standardiser_file)
    ethnicity_classification_collection = ethnicity_classification_collection_from_file(classification_collection_file)

    return EthnicityClassificationFinder(standardiser, ethnicity_classification_collection)


def ethnicity_classification_finder_from_data(standardiser_data, classification_collection_data):
    standardiser = ethnicity_standardiser_from_data(standardiser_data)
    classification_collection = ethnicity_classification_collection_from_data(classification_collection_data)

    return EthnicityClassificationFinder(standardiser, classification_collection)


def ethnicity_standardiser_from_file(file_name):
    standardiser_data = __read_data_from_file_no_headers(file_name)

    return ethnicity_standardiser_from_data(standardiser_data)


def ethnicity_standardiser_from_data(standardiser_data):
    standardiser = EthnicityStandardiser()
    for row in standardiser_data:
        standardiser.add_conversion(raw_ethnicity=row[0], standard_ethnicity=row[1])

    return standardiser


def ethnicity_classification_collection_from_file(file_name):
    classification_file_data = __read_data_from_file_no_headers(file_name)

    return ethnicity_classification_collection_from_data(classification_file_data)


def ethnicity_classification_collection_from_data(collection_data):
    classification_codes = set([row[EthnicityClassificationFileColumn.CODE] for row in collection_data])

    classification_collection = EthnicityClassificationCollection()
    for code in classification_codes:
        classification_collection.add_classification(__classification_from_complete_data(code, collection_data))
    return classification_collection


def ethnicity_classification_collection_from_classification_list(classifications):
    classification_collection = EthnicityClassificationCollection()
    for classification in classifications:
        classification_collection.add_classification(classification)
    return classification_collection


def ethnicity_classification_from_data(code, name, data_rows):
    classification = EthnicityClassification(code=code, name=name)
    for row in data_rows:
        standard_value = row[EthnicityClassificationDataColumn.STANDARD_VALUE]
        classification_data_item = __classification_data_item_from_data(row)
        classification.add_data_item_to_classification(standard_value, classification_data_item)
    return classification


def __classification_data_item_from_data(data_row):
    item_is_required = get_bool(data_row[EthnicityClassificationDataColumn.REQUIRED])
    return EthnicityClassificationDataItem(
        display_ethnicity=data_row[EthnicityClassificationDataColumn.DISPLAY_VALUE],
        parent=data_row[EthnicityClassificationDataColumn.PARENT],
        order=data_row[EthnicityClassificationDataColumn.ORDER],
        required=item_is_required,
    )


def __classification_from_complete_data(classification_code, complete_data):
    this_classification_data = [
        row for row in complete_data if row[EthnicityClassificationFileColumn.CODE] == classification_code
    ]

    classification = EthnicityClassification(
        code=this_classification_data[0][EthnicityClassificationFileColumn.CODE],
        name=this_classification_data[0][EthnicityClassificationFileColumn.NAME],
    )
    for row in this_classification_data:
        data_item = __classification_data_item_from_file_data_row(row)
        classification.add_data_item_to_classification(row[EthnicityClassificationFileColumn.STANDARD_VALUE], data_item)
    return classification


def __classification_data_item_from_file_data_row(file_row):
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
