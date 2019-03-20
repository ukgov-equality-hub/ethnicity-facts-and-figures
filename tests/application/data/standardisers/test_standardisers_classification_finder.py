"""
    The EthnicityClassificationFinder class implements data standardisation functionality.

    It is called from the /get-valid-classifications-for-data endpoint to do backend data calculations

"""
from application.data.standardisers.ethnicity_classification_finder_builder import (
    ethnicity_classification_from_data,
    ethnicity_standardiser_from_data,
    ethnicity_classification_collection_from_classification_list,
    ethnicity_classification_finder_from_file,
)
from application.data.standardisers.ethnicity_classification_finder import EthnicityClassificationFinder


def test_standardiser_does_initialise_with_simple_values():
    # Given
    # simple lookup data
    standardiser_data = [["alpha", "Alpha"], ["aleph", "Alpha"]]

    # When
    # we build a standardiser
    standardiser = ethnicity_standardiser_from_data(standardiser_data)

    # Then
    # an object is returned
    assert standardiser is not None


def test_classfication_does_initialise_with_simple_values():
    # Given
    # simple classification data
    code = "example"
    name = "example"
    data = [["a", "a", "", 0, True], ["b", "b", "", 1, True]]

    # When
    # we build a classification
    classification = ethnicity_classification_from_data(code, name, data)

    # Then
    # an object is returned
    assert classification is not None


def pet_standardiser():
    return ethnicity_standardiser_from_data(
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


def ethnicity_classification_with_cats_and_dogs_data():
    code = "Code1"
    name = "Cats and Dogs"
    classification_rows = [["Cat", "Cat", "Cat", 1, True], ["Dog", "Dog", "Dog", 2, True]]
    return ethnicity_classification_from_data(id=code, name=name, data_rows=classification_rows)


def ethnicity_classification_with_required_fish_cat_and_dog_data():
    code = "Code2"
    name = "Fish and Mammals"
    classification_rows = [
        ["Mammal", "Mammal", "Mammal", 1, False],
        ["Cat", "Cat", "Cat", 2, True],
        ["Dog", "Dog", "Dog", 3, True],
        ["Fish", "Fish", "Fish", 4, True],
    ]
    return ethnicity_classification_from_data(id=code, name=name, data_rows=classification_rows)


def ethnicity_classification_with_required_fish_and_mammal_data():
    code = "Code3"
    name = "Only fish and Mammals"
    classification_rows = [
        ["Mammal", "Mammal", "Mammal", 1, True],
        ["Fish", "Fish", "Fish", 4, True],
        ["Cat", "Cat", "Cat", 2, False],
        ["Dog", "Dog", "Dog", 3, False],
    ]
    return ethnicity_classification_from_data(id=code, name=name, data_rows=classification_rows)


def ethnicity_classification_requires_fish_mammal_and_either_reptile_or_other():
    code = "Code4"
    name = "Standard value Reptile may be used in place of Other"
    classification_rows = [
        ["Mammal", "Mammal", "Mammal", 1, True],
        ["Cat", "Cat", "Mammal", 2, False],
        ["Dog", "Dog", "Mammal", 3, False],
        ["Fish", "Fish", "Fish", 4, True],
        ["Other", "Other", "Other", 5, True],
        ["Reptile", "Other", "Other", 5, True],
    ]
    return ethnicity_classification_from_data(id=code, name=name, data_rows=classification_rows)


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


def test_classification_is_valid_for_data_if_mapping_covers_all_required_values():
    # GIVEN
    # the simple classification from the Cats and Dogs spec
    classification = ethnicity_classification_with_cats_and_dogs_data()
    standard_values = ["Cat", "Dog"]

    # WHEN
    # we validate it
    classification_is_valid = classification.is_valid_for_standard_ethnicities(standard_values)

    # THEN
    # the classification is valid
    assert classification_is_valid is True


def test_classification_is_not_valid_for_data_if_mapping_does_not_cover_all_required_outputs():
    # GIVEN
    # the simple classification from the Cats and Dogs spec
    classification = ethnicity_classification_with_cats_and_dogs_data()
    standard_values_without_dog = ["Cat"]

    # WHEN
    # we validate it
    classification_is_valid = classification.is_valid_for_standard_ethnicities(standard_values_without_dog)

    # THEN
    # the classification is not valid
    assert classification_is_valid is False


def test_classification_is_not_valid_for_data_if_it_includes_unknown_values():
    # GIVEN
    # the simple classification from the Cats and Dogs spec
    classification = ethnicity_classification_with_cats_and_dogs_data()
    standard_values_with_unknown = ["Cat", "Dog", "Fish"]

    # WHEN
    # we validate it
    classification_is_valid = classification.is_valid_for_standard_ethnicities(standard_values_with_unknown)

    # THEN
    # the classification is not valid
    assert classification_is_valid is False


def test_classification_is_valid_for_data_if_it_maps_all_required_data_and_any_optional_data():
    # GIVEN
    # the example classification where 'Cat' 'Dog' and 'Fish' are required but top level category 'Mammal' is not
    classification = ethnicity_classification_with_required_fish_cat_and_dog_data()
    required_values_plus_optional_value = ["Mammal", "Cat", "Dog", "Fish"]

    # WHEN
    # we validate it
    classification_is_valid = classification.is_valid_for_standard_ethnicities(required_values_plus_optional_value)

    # THEN
    # the classification is valid
    assert classification_is_valid is True


def test_classification_functions_correctly_with_raw_data_instead_of_standards():
    # GIVEN
    # the example classification where 'Cat' 'Dog' and 'Fish' are required but top level category 'Mammal' is not
    classification = ethnicity_classification_with_required_fish_cat_and_dog_data()
    standardiser = pet_standardiser()

    # WHEN
    # we validate against data that should map to 'Mammal', 'Cat', 'Dog', 'Fish'
    raw_values = ["Mammal", "FELINE", "Canine  ", "fish  "]
    classification_is_valid = classification.is_valid_for_raw_ethnicities(raw_values, standardiser)

    # THEN
    # the classification is valid
    assert classification_is_valid is True


def test_classification_functions_correctly_with_multiple_rows_of_raw_data():
    # GIVEN
    # the example classification where 'Cat' 'Dog' and 'Fish' are required but top level category 'Mammal' is not
    classification = ethnicity_classification_with_required_fish_cat_and_dog_data()
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
    classification_is_valid = classification.is_valid_for_raw_ethnicities(many_rows_of_raw_data, standardiser)

    # THEN
    # the classification is valid
    assert classification_is_valid is True


def test_classification_outputs_are_an_object_containing_subitems_for_itself_and_a_data_mapping():
    # GIVEN
    # the example classification where 'Cat' 'Dog' and 'Fish' are required but top level category 'Mammal' is not
    classification = ethnicity_classification_with_required_fish_cat_and_dog_data()
    standardiser = pet_standardiser()
    raw_values = ["Mammal", "FELINE", "Canine  ", "fish  "]

    # WHEN
    # we get outputs for
    classification_outputs = classification.get_outputs(raw_values, standardiser)

    # THEN
    # the classification is valid
    assert "classification" in classification_outputs
    assert "data" in classification_outputs


def test_output_returns_top_level_name_and_code_as_part_of_classification_definition():
    # GIVEN
    # the example classification where 'Cat' 'Dog' and 'Fish' are required but top level category 'Mammal' is not
    classification = ethnicity_classification_with_required_fish_cat_and_dog_data()
    standardiser = pet_standardiser()
    raw_values = ["Mammal", "FELINE", "Canine  ", "fish  "]

    # WHEN
    # we get outputs for
    classification_outputs = classification.get_outputs(raw_values, standardiser)

    # THEN
    # the validation is correct
    classification_definition = classification_outputs["classification"]
    assert "Code2" == classification_definition["id"]
    assert "Fish and Mammals" == classification_definition["name"]


def test_output_returns_classification_map_as_part_of_classification_definition():
    # GIVEN
    # the simple classification
    classification = ethnicity_classification_with_cats_and_dogs_data()
    standardiser = pet_standardiser()
    raw_values = ["FELINE", "Canine  "]

    # WHEN
    # we get outputs for
    classification_outputs = classification.get_outputs(raw_values, standardiser)

    # THEN
    # the map is correct
    classification_definition = classification_outputs["classification"]
    expected = {
        "Cat": {"display_ethnicity": "Cat", "parent": "Cat", "order": 1, "required": True},
        "Dog": {"display_ethnicity": "Dog", "parent": "Dog", "order": 2, "required": True},
    }
    assert expected == classification_definition["map"]


def test_output_returns_raw_values_mapped_to_classification_data_items_with_simple_data():
    # GIVEN
    # the simple classification
    classification = ethnicity_classification_with_cats_and_dogs_data()
    standardiser = pet_standardiser()
    raw_values = ["FELINE", "Canine  "]

    # WHEN
    # we get outputs for these raw values
    classification_outputs = classification.get_outputs(raw_values, standardiser)

    # THEN
    # they are mapped to
    classification_mapped_data = classification_outputs["data"]
    expected = [
        {"raw_value": "FELINE", "standard_value": "Cat", "display_value": "Cat", "parent": "Cat", "order": 1},
        {"raw_value": "Canine  ", "standard_value": "Dog", "display_value": "Dog", "parent": "Dog", "order": 2},
    ]
    assert expected == classification_mapped_data


def test_classification_may_use_several_raw_values_to_map_to_a_required_display_value():
    # GIVEN
    # the fish mammal and other classification where standard Other and Reptile both map to display Other
    classification = ethnicity_classification_requires_fish_mammal_and_either_reptile_or_other()
    standardiser = pet_standardiser()
    raw_values_1 = ["Mammal", "Fish", "Other"]
    raw_values_2 = ["Mammal", "Fish", "Reptile"]

    # WHEN
    # we test both for validity using our single classification
    valid_with_other = classification.is_valid_for_raw_ethnicities(raw_values_1, standardiser)
    valid_with_reptile = classification.is_valid_for_raw_ethnicities(raw_values_2, standardiser)

    # THEN
    # we expect both to be valid
    assert valid_with_other is True
    assert valid_with_reptile is True


def test_classification_collection_identifies_valid_classification():
    # GIVEN
    # a simple classification collect
    classification = ethnicity_classification_with_cats_and_dogs_data()
    classification_collection = ethnicity_classification_collection_from_classification_list([classification])
    standardiser = pet_standardiser()
    raw_values = ["Cat", "Dog"]

    # WHEN
    # we request valid classifications
    valid_classifications = classification_collection.get_valid_classifications(raw_values, standardiser)

    # THEN
    # we expect our
    assert 1 == len(valid_classifications)
    assert classification.get_id() == valid_classifications[0].get_id()


def test_classification_collection_can_return_multiple_valid_classifications():
    # GIVEN
    # a collection with two classifications and raw_values that could apply to either
    classification_1 = ethnicity_classification_with_required_fish_cat_and_dog_data()
    classification_2 = ethnicity_classification_with_required_fish_and_mammal_data()

    classification_collection = ethnicity_classification_collection_from_classification_list(
        [classification_1, classification_2]
    )
    standardiser = pet_standardiser()
    raw_values = ["Cat", "Dog", "Fish", "Mammal"]

    # WHEN
    # we request valid classifications
    valid_classifications = classification_collection.get_valid_classifications(raw_values, standardiser)

    # THEN
    # we 2 classifications to have been returned
    assert 2 == len(valid_classifications)


def test_classification_collection_will_not_return_invalid_classifications():
    # GIVEN
    # a collection with two classifications and raw_values that could apply to only the first
    classification_1 = ethnicity_classification_with_required_fish_cat_and_dog_data()
    classification_2 = ethnicity_classification_with_required_fish_and_mammal_data()

    classification_collection = ethnicity_classification_collection_from_classification_list(
        [classification_1, classification_2]
    )
    standardiser = pet_standardiser()
    raw_values = ["Cat", "Dog", "Fish"]

    # WHEN
    # we request valid classifications
    valid_classifications = classification_collection.get_valid_classifications(raw_values, standardiser)

    # THEN
    # only 1 classification is returned
    assert 1 == len(valid_classifications)


def test_classification_finder_given_raw_data_returns_output_for_each_valid_classification_plus_custom():
    # Given
    # a classification search with multiple classifications
    standardiser = pet_standardiser()
    classification_collection = ethnicity_classification_collection_from_classification_list(
        [
            ethnicity_classification_with_required_fish_and_mammal_data(),
            ethnicity_classification_with_required_fish_cat_and_dog_data(),
        ]
    )
    classification_finder = EthnicityClassificationFinder(standardiser, classification_collection)

    # When
    # we search with data that will fit both classifications
    raw_values = ["Cat", "Dog", "Fish", "Mammal"]
    search_outputs = classification_finder.find_classifications(raw_values)

    # Then
    # we expect output from both classifications will be returned (plus the custom classification)
    assert 3 == len(search_outputs)


def test_classification_search_given_raw_data_returns_only_output_for_valid_classifications():
    # Given
    # a classification search with multiple classifications
    standardiser = pet_standardiser()
    classification_collection = ethnicity_classification_collection_from_classification_list(
        [
            ethnicity_classification_with_required_fish_and_mammal_data(),
            ethnicity_classification_with_required_fish_cat_and_dog_data(),
        ]
    )
    classification_finder = EthnicityClassificationFinder(standardiser, classification_collection)

    # When
    # we search with data that will fit only one classification
    raw_values = ["Cat", "Dog", "Fish"]
    search_outputs = classification_finder.find_classifications(raw_values)

    # Then
    # we expect output from one classification will be returned (plus the custom classification)
    assert 2 == len(search_outputs)


def test_classification_search_given_raw_data_returns_data_for_builders():
    # Given
    # a classification search with a simple classifications
    standardiser = pet_standardiser()
    classification_collection = ethnicity_classification_collection_from_classification_list(
        [ethnicity_classification_with_cats_and_dogs_data()]
    )
    classification_finder = EthnicityClassificationFinder(standardiser, classification_collection)

    # When
    # we search with data that will fit the classification
    raw_values = ["FELINE", "Canine  "]
    search_outputs = classification_finder.find_classifications(raw_values)

    # Then
    # we expect the data section will contain data needed to display
    first_classification_data = search_outputs[0]["data"]
    expected = [
        {"raw_value": "FELINE", "standard_value": "Cat", "display_value": "Cat", "parent": "Cat", "order": 1},
        {"raw_value": "Canine  ", "standard_value": "Dog", "display_value": "Dog", "parent": "Dog", "order": 2},
    ]

    assert expected == first_classification_data


def test_classification_search_initialises_from_file():
    # GIVEN
    # the pets data in .csv form
    pets_standardiser_file = "tests/test_data/test_classification_finder/classification_finder_lookup.csv"
    pets_classifications_file = "tests/test_data/test_classification_finder/classification_finder_definitions.csv"

    # WHEN
    # we initialise a classification_finder
    classification_finder = ethnicity_classification_finder_from_file(pets_standardiser_file, pets_classifications_file)

    # THEN
    # we have a valid generator
    assert classification_finder is not None

    # that standardises as we expect
    cat_dog_fish_classifications = classification_finder.find_classifications(["feline", "canine", "fish"])
    assert cat_dog_fish_classifications[0]["classification"]["name"] == "Fish and Mammals"
    assert cat_dog_fish_classifications[0]["data"][0] == {
        "raw_value": "feline",
        "standard_value": "Cat",
        "display_value": "Cat",
        "parent": "Mammal",
        "order": "2",
    }
