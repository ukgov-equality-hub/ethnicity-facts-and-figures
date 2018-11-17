from application.data.standardisers.ethnicity_classification_finder import (
    EthnicityStandardiser,
    EthnicityClassificationCollection,
    EthnicityClassification,
    EthnicityClassificationDataItem,
    EthnicityClassificationFinder,
)
from application.utils import get_bool
from application.data.standardisers.ethnicity_classification_finder import EthnicityClassificationFinder
from application.data.standardisers.ethnicity_classification_finder import EthnicityStandardiser
from typing import List
from application.data.standardisers.ethnicity_classification_finder import EthnicityClassificationCollection
from application.data.standardisers.ethnicity_classification_finder import EthnicityClassification
from typing import Any
from typing import Optional
from typing import Union
from application.data.standardisers.ethnicity_classification_finder import EthnicityClassificationDataItem
from mypy_extensions import NoReturn


class EthnicityClassificationFileColumn:
    """
    An enum that defines columns when loading an EthnicityClassificationFinder from a settings file
    """

    ID = 0
    SHORT_NAME = 1
    LONG_NAME = 2
    STANDARD_VALUE = 3
    DISPLAY_VALUE = 4
    PARENT = 5
    ORDER = 6
    REQUIRED = 7


class EthnicityClassificationDataColumn:
    """
    An enum that defines columns when loading an EthnicityClassification from data (i.e. a list of lists)
    """

    STANDARD_VALUE = 0
    DISPLAY_VALUE = 1
    PARENT = 2
    ORDER = 3
    REQUIRED = 4


def ethnicity_classification_finder_from_file(
    standardiser_file: str, classification_collection_file: str
) -> EthnicityClassificationFinder:
    standardiser = ethnicity_standardiser_from_file(standardiser_file)
    ethnicity_classification_collection = ethnicity_classification_collection_from_file(classification_collection_file)

    return EthnicityClassificationFinder(standardiser, ethnicity_classification_collection)


def ethnicity_classification_finder_from_data(standardiser_data, classification_collection_data):
    standardiser = ethnicity_standardiser_from_data(standardiser_data)
    classification_collection = ethnicity_classification_collection_from_data(classification_collection_data)

    return EthnicityClassificationFinder(standardiser, classification_collection)


def ethnicity_standardiser_from_file(file_name: str) -> EthnicityStandardiser:
    standardiser_data = __read_data_from_file_no_headers(file_name)

    return ethnicity_standardiser_from_data(standardiser_data)


def ethnicity_standardiser_from_data(standardiser_data: List[List[str]]) -> EthnicityStandardiser:
    standardiser = EthnicityStandardiser()
    for row in standardiser_data:
        standardiser.add_conversion(raw_ethnicity=row[0], standard_ethnicity=row[1])

    return standardiser


def ethnicity_classification_collection_from_file(file_name: str) -> EthnicityClassificationCollection:
    classification_file_data = __read_data_from_file_no_headers(file_name)

    return ethnicity_classification_collection_from_data(classification_file_data)


def ethnicity_classification_collection_from_data(
    collection_data: List[List[str]]
) -> EthnicityClassificationCollection:
    classification_ids = set([row[EthnicityClassificationFileColumn.ID] for row in collection_data])

    classification_collection = EthnicityClassificationCollection()
    for classification_id in classification_ids:
        classification_collection.add_classification(
            __classification_from_complete_data(classification_id, collection_data)
        )
    return classification_collection


def ethnicity_classification_collection_from_classification_list(
    classifications: List[EthnicityClassification]
) -> EthnicityClassificationCollection:
    classification_collection = EthnicityClassificationCollection()
    for classification in classifications:
        classification_collection.add_classification(classification)
    return classification_collection


def ethnicity_classification_from_data(
    id: str, name: str, data_rows: List[List[Union[int, str]]], long_name: Optional[Any] = None
) -> EthnicityClassification:
    if long_name is None:
        classification_long_name = name
    else:
        classification_long_name = long_name

    classification = EthnicityClassification(id=id, name=name, long_name=name)
    for row in data_rows:
        standard_value = row[EthnicityClassificationDataColumn.STANDARD_VALUE]
        classification_data_item = __classification_data_item_from_data(row)
        classification.add_data_item_to_classification(standard_value, classification_data_item)
    return classification


def __classification_data_item_from_data(data_row: List[Union[int, str]]) -> EthnicityClassificationDataItem:
    item_is_required = get_bool(data_row[EthnicityClassificationDataColumn.REQUIRED])
    return EthnicityClassificationDataItem(
        display_ethnicity=data_row[EthnicityClassificationDataColumn.DISPLAY_VALUE],
        parent=data_row[EthnicityClassificationDataColumn.PARENT],
        order=data_row[EthnicityClassificationDataColumn.ORDER],
        required=item_is_required,
    )


def __classification_from_complete_data(
    classification_id: str, complete_data: List[List[str]]
) -> EthnicityClassification:
    this_classification_data = [
        row for row in complete_data if row[EthnicityClassificationFileColumn.ID] == classification_id
    ]

    classification = EthnicityClassification(
        id=this_classification_data[0][EthnicityClassificationFileColumn.ID],
        name=this_classification_data[0][EthnicityClassificationFileColumn.SHORT_NAME],
        long_name=this_classification_data[0][EthnicityClassificationFileColumn.LONG_NAME],
    )
    for row in this_classification_data:
        data_item = __classification_data_item_from_file_data_row(row)
        classification.add_data_item_to_classification(row[EthnicityClassificationFileColumn.STANDARD_VALUE], data_item)
    return classification


def __classification_data_item_from_file_data_row(file_row: List[str]) -> EthnicityClassificationDataItem:
    item_is_required = get_bool(file_row[EthnicityClassificationFileColumn.REQUIRED])
    return EthnicityClassificationDataItem(
        display_ethnicity=file_row[EthnicityClassificationFileColumn.DISPLAY_VALUE],
        parent=file_row[EthnicityClassificationFileColumn.PARENT],
        order=file_row[EthnicityClassificationFileColumn.ORDER],
        required=item_is_required,
    )


def __read_data_from_file_no_headers(file_name: str) -> NoReturn:
    import csv

    with open(file_name, "r") as f:
        reader = csv.reader(f)
        data = list(reader)
        if len(data) > 1:
            return data[1:]
    return []
