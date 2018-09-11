"""
    The EthnicityClassificationFinder class implements data standardisation functionality.

    It is called from the /get-valid-presets-for-data endpoint to do backend data calculations

"""
from application.data.standardisers.preset_builder import (
    preset_from_data,
    standardiser_from_data,
    preset_collection_from_preset_list,
    preset_search_from_file,
)
from application.data.standardisers.ethnicity_classification_finder import EthnicityClassificationFinder


def test_standardiser_does_initialise_with_simple_values():
    # Given
    # simple lookup data
    standardiser_data = [["alpha", "Alpha"], ["aleph", "Alpha"]]

    # When
    # we build a standardiser
    standardiser = standardiser_from_data(standardiser_data)

    # Then
    # an object is returned
    assert standardiser is not None


def test_preset_does_initialise_with_simple_values():
    # Given
    # simple preset data
    code = "example"
    name = "example"
    data = [["a", "a", "", 0, True], ["b", "b", "", 1, True]]

    # When
    # we build a preset
    preset = preset_from_data(code, name, data)

    # Then
    # an object is returned
    assert preset is not None


def pet_standardiser():
    return standardiser_from_data(
        [
            ["mammal", "Mammal"],
            ["cat", "Cat"],
            ["feline", "Cat"],
            ["dog", "Dog"],
            ["canine", "Dog"],
            ["fish", "Fish"],
            ["reptile", "Reptile"],
            ["other", "Other"],
        ]
    )


def preset_with_cats_and_dogs_data():
    code = "Code1"
    name = "Cats and Dogs"
    preset_rows = [["Cat", "Cat", "Cat", 1, True], ["Dog", "Dog", "Dog", 2, True]]
    return preset_from_data(code=code, name=name, data_rows=preset_rows)


def preset_with_required_fish_cat_and_dog_data():
    code = "Code2"
    name = "Fish and Mammals"
    preset_rows = [
        ["Mammal", "Mammal", "Mammal", 1, False],
        ["Cat", "Cat", "Cat", 2, True],
        ["Dog", "Dog", "Dog", 3, True],
        ["Fish", "Fish", "Fish", 4, True],
    ]
    return preset_from_data(code=code, name=name, data_rows=preset_rows)


def preset_with_required_fish_and_mammal_data():
    code = "Code3"
    name = "Only fish and Mammals"
    preset_rows = [
        ["Mammal", "Mammal", "Mammal", 1, True],
        ["Fish", "Fish", "Fish", 4, True],
        ["Cat", "Cat", "Cat", 2, False],
        ["Dog", "Dog", "Dog", 3, False],
    ]
    return preset_from_data(code=code, name=name, data_rows=preset_rows)


def preset_requires_fish_mammal_and_either_reptile_or_other():
    code = "Code4"
    name = "Standard value Reptile may be used in place of Other"
    preset_rows = [
        ["Mammal", "Mammal", "Mammal", 1, True],
        ["Cat", "Cat", "Mammal", 2, False],
        ["Dog", "Dog", "Mammal", 3, False],
        ["Fish", "Fish", "Fish", 4, True],
        ["Other", "Other", "Other", 5, True],
        ["Reptile", "Other", "Other", 5, True],
    ]
    return preset_from_data(code=code, name=name, data_rows=preset_rows)


def test_standardiser_does_convert_correct_value():
    # GIVEN
    # the pet standardiser
    standardiser = pet_standardiser()

    # WHEN
    # standardiser converts a value that is correct
    actual = "feline"
    converted = standardiser.standardise(actual)

    # THEN
    # the value is the expected one
    expected = "Cat"
    assert expected == converted


def test_standardiser_does_trim_input():
    # GIVEN
    # the pet standardiser
    standardiser = pet_standardiser()

    # WHEN
    # standardiser converts a value with white space
    actual = "feline     "
    converted = standardiser.standardise(actual)

    # THEN
    # the value is the expected one
    expected = "Cat"
    assert expected == converted


def test_standardiser_is_case_insensitive():
    # GIVEN
    # the pet standardiser
    standardiser = pet_standardiser()

    # WHEN
    # standardiser converts a value with upper case letters
    actual = "FELINE"
    converted = standardiser.standardise(actual)

    # THEN
    # the value is the expected one
    expected = "Cat"
    assert expected == converted


def test_standardiser_does_not_convert_unknown_value():
    # GIVEN
    # the pet standardiser
    standardiser = pet_standardiser()

    # WHEN
    # standardiser converts a value with an unknown value
    actual = "cathedral"
    converted = standardiser.standardise(actual)

    # THEN
    # the value is the expected one
    expected = "cathedral"
    assert expected == converted


def test_standardiser_does_convert_a_list_of_values():
    # GIVEN
    # the pet standardiser
    standardiser = pet_standardiser()

    # WHEN
    # standardiser converts a value with an unknown value
    actual = ["feline", "cat", "cat", "dog", "canine"]
    converted = standardiser.standardise_all(actual)

    # THEN
    # the value is the expected one
    expected = ["Cat", "Cat", "Cat", "Dog", "Dog"]
    assert expected == converted


def test_preset_is_valid_for_data_if_mapping_covers_all_required_values():
    # GIVEN
    # the simple preset from the Cats and Dogs spec
    preset = preset_with_cats_and_dogs_data()
    standard_values = ["Cat", "Dog"]

    # WHEN
    # we validate it
    preset_is_valid = preset.is_valid_for_standard_ethnicities(standard_values)

    # THEN
    # the preset is valid
    assert preset_is_valid is True


def test_preset_is_not_valid_for_data_if_mapping_does_not_cover_all_required_outputs():
    # GIVEN
    # the simple preset from the Cats and Dogs spec
    preset = preset_with_cats_and_dogs_data()
    standard_values_without_dog = ["Cat"]

    # WHEN
    # we validate it
    preset_is_valid = preset.is_valid_for_standard_ethnicities(standard_values_without_dog)

    # THEN
    # the preset is not valid
    assert preset_is_valid is False


def test_preset_is_not_valid_for_data_if_it_includes_unknown_values():
    # GIVEN
    # the simple preset from the Cats and Dogs spec
    preset = preset_with_cats_and_dogs_data()
    standard_values_with_unknown = ["Cat", "Dog", "Fish"]

    # WHEN
    # we validate it
    preset_is_valid = preset.is_valid_for_standard_ethnicities(standard_values_with_unknown)

    # THEN
    # the preset is not valid
    assert preset_is_valid is False


def test_preset_is_valid_for_data_if_it_maps_all_required_data_and_any_optional_data():
    # GIVEN
    # the example preset where 'Cat' 'Dog' and 'Fish' are required but top level category 'Mammal' is not
    preset = preset_with_required_fish_cat_and_dog_data()
    required_values_plus_optional_value = ["Mammal", "Cat", "Dog", "Fish"]

    # WHEN
    # we validate it
    preset_is_valid = preset.is_valid_for_standard_ethnicities(required_values_plus_optional_value)

    # THEN
    # the preset is valid
    assert preset_is_valid is True


def test_preset_functions_correctly_with_raw_data_instead_of_standards():
    # GIVEN
    # the example preset where 'Cat' 'Dog' and 'Fish' are required but top level category 'Mammal' is not
    preset = preset_with_required_fish_cat_and_dog_data()
    standardiser = pet_standardiser()

    # WHEN
    # we validate against data that should map to 'Mammal', 'Cat', 'Dog', 'Fish'
    raw_values = ["Mammal", "FELINE", "Canine  ", "fish  "]
    preset_is_valid = preset.is_valid_for_raw_ethnicities(raw_values, standardiser)

    # THEN
    # the preset is valid
    assert preset_is_valid is True


def test_preset_functions_correctly_with_multiple_rows_of_raw_data():
    # GIVEN
    # the example preset where 'Cat' 'Dog' and 'Fish' are required but top level category 'Mammal' is not
    preset = preset_with_required_fish_cat_and_dog_data()
    standardiser = pet_standardiser()

    # WHEN
    # we validate against data that should map to 'Mammal', 'Cat', 'Dog', 'Fish'
    many_rows_of_raw_data = [
        "Mammal",
        "FELINE",
        "Canine  ",
        "fish  ",
        "Mammal",
        "FELINE",
        "Canine  ",
        "fish  ",
        "Mammal",
        "FELINE",
        "Canine  ",
        "fish  ",
        "Mammal",
        "FELINE",
        "Canine  ",
        "fish  ",
    ]
    preset_is_valid = preset.is_valid_for_raw_ethnicities(many_rows_of_raw_data, standardiser)

    # THEN
    # the preset is valid
    assert preset_is_valid is True


def test_preset_outputs_are_an_object_containing_subitems_for_itself_and_a_data_mapping():
    # GIVEN
    # the example preset where 'Cat' 'Dog' and 'Fish' are required but top level category 'Mammal' is not
    preset = preset_with_required_fish_cat_and_dog_data()
    standardiser = pet_standardiser()
    raw_values = ["Mammal", "FELINE", "Canine  ", "fish  "]

    # WHEN
    # we get outputs for
    preset_outputs = preset.get_outputs(raw_values, standardiser)

    # THEN
    # the preset is valid
    assert "classification" in preset_outputs
    assert "data" in preset_outputs


def test_output_returns_top_level_name_and_code_as_part_of_preset_definition():
    # GIVEN
    # the example preset where 'Cat' 'Dog' and 'Fish' are required but top level category 'Mammal' is not
    preset = preset_with_required_fish_cat_and_dog_data()
    standardiser = pet_standardiser()
    raw_values = ["Mammal", "FELINE", "Canine  ", "fish  "]

    # WHEN
    # we get outputs for
    preset_outputs = preset.get_outputs(raw_values, standardiser)

    # THEN
    # the validation is correct
    preset_definition = preset_outputs["classification"]
    assert "Code2" == preset_definition["code"]
    assert "Fish and Mammals" == preset_definition["name"]


def test_output_returns_preset_map_as_part_of_preset_definition():
    # GIVEN
    # the simple preset
    preset = preset_with_cats_and_dogs_data()
    standardiser = pet_standardiser()
    raw_values = ["FELINE", "Canine  "]

    # WHEN
    # we get outputs for
    preset_outputs = preset.get_outputs(raw_values, standardiser)

    # THEN
    # the map is correct
    preset_definition = preset_outputs["classification"]
    expected = {
        "Cat": {"display_ethnicity": "Cat", "parent": "Cat", "order": 1, "required": True},
        "Dog": {"display_ethnicity": "Dog", "parent": "Dog", "order": 2, "required": True},
    }
    assert expected == preset_definition["map"]


def test_output_returns_raw_values_mapped_to_presets_with_simple_data():
    # GIVEN
    # the simple preset
    preset = preset_with_cats_and_dogs_data()
    standardiser = pet_standardiser()
    raw_values = ["FELINE", "Canine  "]

    # WHEN
    # we get outputs for these raw values
    preset_outputs = preset.get_outputs(raw_values, standardiser)

    # THEN
    # they are mapped to
    preset_mapped_data = preset_outputs["data"]
    expected = [
        {"raw_value": "FELINE", "standard_value": "Cat", "display_value": "Cat", "parent": "Cat", "order": 1},
        {"raw_value": "Canine  ", "standard_value": "Dog", "display_value": "Dog", "parent": "Dog", "order": 2},
    ]
    assert expected == preset_mapped_data


def test_preset_may_use_several_raw_values_to_map_to_a_required_display_value():
    # GIVEN
    # the fish mammal and other preset where standard Other and Reptile both map to display Other
    preset = preset_requires_fish_mammal_and_either_reptile_or_other()
    standardiser = pet_standardiser()
    raw_values_1 = ["Mammal", "Fish", "Other"]
    raw_values_2 = ["Mammal", "Fish", "Reptile"]

    # WHEN
    # we test both for validity using our single preset
    valid_with_other = preset.is_valid_for_raw_ethnicities(raw_values_1, standardiser)
    valid_with_reptile = preset.is_valid_for_raw_ethnicities(raw_values_2, standardiser)

    # THEN
    # we expect both to be valid
    assert valid_with_other is True
    assert valid_with_reptile is True


def test_preset_collection_identifies_valid_preset():
    # GIVEN
    # a simple preset collect
    preset = preset_with_cats_and_dogs_data()
    preset_collection = preset_collection_from_preset_list([preset])
    standardiser = pet_standardiser()
    raw_values = ["Cat", "Dog"]

    # WHEN
    # we request valid presets
    valid_presets = preset_collection.get_valid_classifications(raw_values, standardiser)

    # THEN
    # we expect our
    assert 1 == len(valid_presets)
    assert preset.get_code() == valid_presets[0].get_code()


def test_preset_collection_can_return_multiple_valid_presets():
    # GIVEN
    # a collection with two presets and raw_values that could apply to either
    preset_1 = preset_with_required_fish_cat_and_dog_data()
    preset_2 = preset_with_required_fish_and_mammal_data()

    preset_collection = preset_collection_from_preset_list([preset_1, preset_2])
    standardiser = pet_standardiser()
    raw_values = ["Cat", "Dog", "Fish", "Mammal"]

    # WHEN
    # we request valid presets
    valid_presets = preset_collection.get_valid_classifications(raw_values, standardiser)

    # THEN
    # we 2 presets to have been returned
    assert 2 == len(valid_presets)


def test_preset_collection_will_not_return_invalid_presets():
    # GIVEN
    # a collection with two presets and raw_values that could apply to only the first
    preset_1 = preset_with_required_fish_cat_and_dog_data()
    preset_2 = preset_with_required_fish_and_mammal_data()

    preset_collection = preset_collection_from_preset_list([preset_1, preset_2])
    standardiser = pet_standardiser()
    raw_values = ["Cat", "Dog", "Fish"]

    # WHEN
    # we request valid presets
    valid_presets = preset_collection.get_valid_classifications(raw_values, standardiser)

    # THEN
    # only 1 preset is returned
    assert 1 == len(valid_presets)


def test_preset_search_given_raw_data_returns_preset_outputs():
    # Given
    # a preset search with multiple presets
    standardiser = pet_standardiser()
    preset_collection = preset_collection_from_preset_list(
        [preset_with_required_fish_and_mammal_data(), preset_with_required_fish_cat_and_dog_data()]
    )
    preset_search = EthnicityClassificationFinder(standardiser, preset_collection)

    # When
    # we search with data that will fit both presets
    raw_values = ["Cat", "Dog", "Fish", "Mammal"]
    search_outputs = preset_search.find_classifications(raw_values)

    # Then
    # we expect output from both presets will be returned (plus the custom preset)
    assert 3 == len(search_outputs)


def test_preset_search_given_raw_data_returns_only_presets():
    # Given
    # a preset search with multiple presets
    standardiser = pet_standardiser()
    preset_collection = preset_collection_from_preset_list(
        [preset_with_required_fish_and_mammal_data(), preset_with_required_fish_cat_and_dog_data()]
    )
    preset_search = EthnicityClassificationFinder(standardiser, preset_collection)

    # When
    # we search with data that will fit only one preset
    raw_values = ["Cat", "Dog", "Fish"]
    search_outputs = preset_search.find_classifications(raw_values)

    # Then
    # we expect output from one preset will be returned (plus the custom preset)
    assert 2 == len(search_outputs)


def test_preset_search_given_raw_data_returns_data_for_builders_v2():
    # Given
    # a preset search with a simple presets
    standardiser = pet_standardiser()
    preset_collection = preset_collection_from_preset_list([preset_with_cats_and_dogs_data()])
    preset_search = EthnicityClassificationFinder(standardiser, preset_collection)

    # When
    # we search with data that will fit the preset
    raw_values = ["FELINE", "Canine  "]
    search_outputs = preset_search.find_classifications(raw_values)

    # Then
    # we expect the data section will contain data needed to display
    first_preset_data = search_outputs[0]["data"]
    expected = [
        {"raw_value": "FELINE", "standard_value": "Cat", "display_value": "Cat", "parent": "Cat", "order": 1},
        {"raw_value": "Canine  ", "standard_value": "Dog", "display_value": "Dog", "parent": "Dog", "order": 2},
    ]

    assert expected == first_preset_data


def test_preset_search_initialises_from_file():
    # GIVEN
    # the pets data in .csv form
    pets_standardiser_file = "tests/test_data/test_preset_search/standardiser_lookup.csv"
    pets_preset_1_and_2_file = "tests/test_data/test_preset_search/preset_definitions.csv"

    # WHEN
    # we initialise a preset_search
    preset_search = preset_search_from_file(pets_standardiser_file, pets_preset_1_and_2_file)

    # THEN
    # we have a valid generator
    assert preset_search is not None

    # that standardises as we expect
    cat_dog_fish_presets = preset_search.find_classifications(["feline", "canine", "fish"])
    assert cat_dog_fish_presets[0]["classification"]["name"] == "Fish and Mammals"
    assert cat_dog_fish_presets[0]["data"][0] == {
        "raw_value": "feline",
        "standard_value": "Cat",
        "display_value": "Cat",
        "parent": "Mammal",
        "order": "2",
    }
