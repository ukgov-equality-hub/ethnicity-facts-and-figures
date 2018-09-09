from application.data.standardisers.preset_search import (
    Standardiser,
    PresetCollection,
    Preset,
    PresetDataItem,
    PresetSearch,
)
from application.utils import get_bool


def preset_search_from_file(standardiser_file, preset_collection_file):
    standardiser = standardiser_from_file(standardiser_file)
    preset_collection = preset_collection_from_file(preset_collection_file)

    return PresetSearch(standardiser, preset_collection)


def preset_search_from_data(standardiser_data, preset_collection_data):
    standardiser = standardiser_from_data(standardiser_data)
    preset_collection = preset_collection_from_data(preset_collection_data)

    return PresetSearch(standardiser, preset_collection)


def standardiser_from_file(file_name):
    standardiser_data = __read_data_from_file_no_headers(file_name)

    return standardiser_from_data(standardiser_data)


def standardiser_from_data(standardiser_data):
    standardiser = Standardiser()
    for row in standardiser_data:
        standardiser.add_conversion(raw_ethnicity=row[0], standard_ethnicity=row[1])

    return standardiser


def preset_collection_from_file(file_name):
    preset_file_data = __read_data_from_file_no_headers(file_name)

    return preset_collection_from_data(preset_file_data)


def preset_collection_from_data(collection_data):
    preset_codes = set([row[PresetFileDefinition.CODE] for row in collection_data])

    preset_collection = PresetCollection()
    for code in preset_codes:
        preset_collection.add_preset(__preset_from_complete_data(code, collection_data))
    return preset_collection


def preset_collection_from_preset_list(presets):
    preset_collection = PresetCollection()
    for preset in presets:
        preset_collection.add_preset(preset)
    return preset_collection


def preset_from_data(code, name, data_rows):
    preset = Preset(code=code, name=name)
    for row in data_rows:
        standard_value = row[PresetDataDefinition.STANDARD_VALUE]
        preset_item = __preset_data_item_from_data(row)
        preset.add_data_item_to_preset(standard_value, preset_item)
    return preset


def __preset_data_item_from_data(data_row):
    item_is_required = get_bool(data_row[PresetDataDefinition.REQUIRED])
    return PresetDataItem(
        display_ethnicity=data_row[PresetDataDefinition.DISPLAY_VALUE],
        parent=data_row[PresetDataDefinition.PARENT],
        order=data_row[PresetDataDefinition.ORDER],
        required=item_is_required,
    )


def __preset_from_complete_data(preset_code, complete_data):
    this_preset_data = [row for row in complete_data if row[PresetFileDefinition.CODE] == preset_code]

    preset = Preset(
        code=this_preset_data[0][PresetFileDefinition.CODE], name=this_preset_data[0][PresetFileDefinition.NAME]
    )
    for row in this_preset_data:
        data_item = __preset_data_item_from_file_data_row(row)
        preset.add_data_item_to_preset(row[PresetFileDefinition.STANDARD_VALUE], data_item)
    return preset


def __preset_data_item_from_file_data_row(file_row):
    item_is_required = get_bool(file_row[PresetFileDefinition.REQUIRED])
    return PresetDataItem(
        display_ethnicity=file_row[PresetFileDefinition.DISPLAY_VALUE],
        parent=file_row[PresetFileDefinition.PARENT],
        order=file_row[PresetFileDefinition.ORDER],
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


class PresetFileDefinition:
    CODE = 0
    NAME = 1
    STANDARD_VALUE = 2
    DISPLAY_VALUE = 3
    PARENT = 4
    ORDER = 5
    REQUIRED = 6


class PresetDataDefinition:
    STANDARD_VALUE = 0
    DISPLAY_VALUE = 1
    PARENT = 2
    ORDER = 3
    REQUIRED = 4
