"""
    The AutoDataGenerator class implements data standardisation functionality.

    For Ethnicity Facts & Figures it will identify a data set uses, say, ONS 16+1 categorisation and return
    an enriched set of values with metadata to sort and display the content as a chart or table

    The autodata it refers to are extra data attributes that can be derived from the ethnicity value in a row
    These include the default standardised version of that ethnicity, the standardised version in the
    context of a preset, the parent value for that ethnicity and the order it should appear

    'Presets' are definitions of how to display and order a set of values.
    By checking that all values in a list can be covered by a preset and all necessary preset values are covered
    we can say whether the preset is valid for displaying a list of data
    Typically any given list of values will only have one valid preset but it is possible to have several.
    This is particularly true in 5+1 categorisations

    It is called from the /get-valid-presets-for-data endpoint to do backend data calculations

"""

from application.cms.data_utils import AutoDataGenerator


def test_preset_service_does_initialise():
    preset_service = AutoDataGenerator(standardiser_lookup=[], preset_lookup=[])

    assert preset_service is not None


def test_preset_service_does_initialise_with_simple_values():
    # GIVEN
    # some simple data
    standardiser_data = [['alpha', 'Alpha'], ['aleph', 'Alpha']]
    preset_data = [['alpha', 'a', 'a', '', 0, True],
                   ['alpha', 'b', 'b', '', 1, True],
                   ['beta', 'a', 'a', '', 0, True],
                   ['beta', 'b', 'b', '', 1, True]]

    # WHEN
    # we initialise the service
    preset_service = AutoDataGenerator(standardiser_lookup=standardiser_data,
                                       preset_lookup=preset_data)

    # THEN
    # the service variables are set
    assert len(preset_service.standards) == 2
    assert len(preset_service.presets) == 2


def pet_standards():
    return [
        ['mammal', 'Mammal'],
        ['cat', 'Cat'], ['feline', 'Cat'],
        ['dog', 'Dog'], ['canine', 'Dog'],
        ['fish', 'Fish'],
        ['reptile', 'Reptile'],
        ['other', 'Other']
    ]


def preset_cats_and_dogs_data():
    return [['Cats and Dogs', 'Cat', 'Cat', 'Cat', 1, True],
            ['Cats and Dogs', 'Dog', 'Dog', 'Dog', 2, True]]


def preset_fish_and_mammal_parent_child_data():
    return [
        ['Fish and Mammals', 'Mammal', 'Mammal', 'Mammal', 1, False],
        ['Fish and Mammals', 'Cat', 'Cat', 'Mammal', 2, True],
        ['Fish and Mammals', 'Dog', 'Dog', 'Mammal', 3, True],
        ['Fish and Mammals', 'Fish', 'Fish', 'Fish', 4, True],
    ]


def preset_fish_mammal_other_data():
    return [
        ['Fish, Mammal, Other', 'Mammal', 'Mammal', 'Mammal', 1, True],
        ['Fish, Mammal, Other', 'Cat', 'Cat', 'Mammal', 2, False],
        ['Fish, Mammal, Other', 'Dog', 'Dog', 'Mammal', 3, False],
        ['Fish, Mammal, Other', 'Fish', 'Fish', 'Fish', 4, True],
        ['Fish, Mammal, Other', 'Other', 'Other', 'Other', 5, True],
        ['Fish, Mammal, Other', 'Reptile', 'Other', 'Other', 5, True]
    ]


def test_standardiser_does_convert_correct_value():
    # GIVEN
    # the pet standardiser
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_cats_and_dogs_data())

    # WHEN
    # standardiser converts a value that is correct
    actual = ['feline']
    converted = auto_data_generator.convert_to_standard_data(actual)

    # THEN
    # the value is the expected one
    expected = [{'value': 'feline', 'standard': 'Cat'}]
    assert converted == expected


def test_standardiser_does_trim_input():
    # GIVEN
    # the pet standardiser
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_cats_and_dogs_data())

    # WHEN
    # standardiser converts a value that is correct
    actual = ['feline       ']
    converted = auto_data_generator.convert_to_standard_data(actual)

    # THEN
    # the value is the expected one
    expected = [{'value': 'feline       ', 'standard': 'Cat'}]
    assert converted == expected


def test_standardiser_is_case_insensitive_input():
    # GIVEN
    # the pet standardiser
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_cats_and_dogs_data())

    # WHEN
    # standardiser converts a value that is correct
    actual = ['FELINE']
    converted = auto_data_generator.convert_to_standard_data(actual)

    # THEN
    # the value is the expected one
    expected = [{'value': 'FELINE', 'standard': 'Cat'}]
    assert converted == expected


def test_standardiser_does_not_convert_unknown_value():
    # GIVEN
    # the pet standardiser
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_cats_and_dogs_data())

    # WHEN
    # standardiser tries to converts a value that is not present
    actual = ['cathedral']
    converted = auto_data_generator.convert_to_standard_data(actual)

    # THEN
    # it maintains the original values
    expected = [{'value': 'cathedral', 'standard': 'cathedral'}]
    assert converted == expected


def test_standardiser_does_convert_a_list_of_values():
    # GIVEN
    # the pet standardiser
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_cats_and_dogs_data())

    # WHEN
    # standardiser converts a value that is correct
    actual = ['feline', 'cat', 'cat', 'dog', 'canine']
    converted = auto_data_generator.convert_to_standard_data(actual)

    # THEN
    # the value is the expected one
    expected = [{'value': 'feline', 'standard': 'Cat'},
                {'value': 'cat', 'standard': 'Cat'},
                {'value': 'cat', 'standard': 'Cat'},
                {'value': 'dog', 'standard': 'Dog'},
                {'value': 'canine', 'standard': 'Dog'}]
    assert converted == expected


def test_preset_valid_if_it_covers_all_values():
    # GIVEN
    # preset build from the Cats and Dogs spec
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_cats_and_dogs_data())

    # WHEN
    # we validate it against the values Cat and Dog
    values = ['Cat', 'Dog']
    valid_presets = auto_data_generator.get_valid_presets_for_data(values)

    # THEN
    # the validation is correct
    assert valid_presets != []


def test_preset_invalid_if_it_does_not_cover_values():
    # GIVEN
    # preset which includes Cat and Dog only
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_cats_and_dogs_data())

    # WHEN
    # we validate it against the value Velociraptor
    values = ['Cat', 'Velociraptor']
    valid_presets = auto_data_generator.get_valid_presets_for_data(values)

    # THEN
    # the validation fails
    assert valid_presets == []


def test_multiple_presets_reduce_to_valid_ones():
    # GIVEN
    # preset build from the two different specs
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)

    # WHEN
    # we validate it against the values Cat, Dog and Fish
    cat_dog_fish_valid_presets = auto_data_generator.get_valid_presets_for_data(['Cat', 'Dog', 'Fish'])
    cat_velociraptor_valid_presets = auto_data_generator.get_valid_presets_for_data(['Cat', 'Velociraptor'])

    # THEN
    # the validation is correct
    assert len(cat_dog_fish_valid_presets) == 1
    assert len(cat_velociraptor_valid_presets) == 0


def test_multiple_presets_exclude_invalid_ones_due_to_unclassified_value():
    # GIVEN
    # preset build from the two different specs
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)
    assert len(auto_data_generator.presets) == 2

    # WHEN
    # we validate it against the values Cat, Dog and Fish
    mammal_cat_dog_fish_valid_presets = auto_data_generator.get_valid_presets_for_data(['Mammal', 'Cat', 'Dog', 'Fish'])

    # THEN
    # fish is not classified by `cats and dogs` preset
    # we expect only the `fish and mammals` preset to be valid
    assert len(mammal_cat_dog_fish_valid_presets) == 1


def test_multiple_presets_exclude_invalid_ones_due_to_missing_required_value():
    # GIVEN
    # preset build from the two different specs
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)
    assert len(auto_data_generator.presets) == 2

    # WHEN
    # we validate it against the values Cat, Dog
    cat_dog_presets = auto_data_generator.get_valid_presets_for_data(['Cat', 'Dog'])

    # THEN
    # required value fish for `fish and mammals` is not present
    # so we expect only the `cats and dogs` preset to be valid
    assert len(cat_dog_presets) == 1


def test_multiple_presets_does_not_exclude_valid_ones_due_to_missing_not_required_value():
    # GIVEN
    # preset built from the two different specs
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)
    assert len(auto_data_generator.presets) == 2

    # WHEN
    # we validate it against the values Cat, Dog, Fish
    cat_dog_presets = auto_data_generator.get_valid_presets_for_data(['Fish', 'Cat', 'Dog'])

    # THEN
    # Mammal is not present but it is not a required value so...
    # `fish and mammals` is valid
    assert len(cat_dog_presets) == 1


def test_multiple_presets_include_all_valid_ones():
    # TODO test where we expect multiple presets to be returned

    # GIVEN
    # preset build from the two different specs
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)
    assert len(auto_data_generator.presets) == 2

    # WHEN
    # we validate it against the values Cat, Dog and Fish
    cat_dog_valid_presets = auto_data_generator.get_valid_presets_for_data(['Cat', 'Dog'])

    # THEN
    # we expect both presets to be valid
    # assert len(cat_dog_valid_presets) == 2


def test_build_auto_data_returns_set_of_auto_data_for_each_valid_preset():
    # TODO test where we expect multiple presets to be returned
    # GIVEN
    # preset build from the two different specs
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)
    assert len(auto_data_generator.presets) == 2

    # WHEN
    # we convert values with multiple valid preset specs
    cat_dog_auto_data = auto_data_generator.build_auto_data(['cat', 'dog'])
    cat_dog_fish_auto_data = auto_data_generator.build_auto_data(['cat', 'dog', 'fish'])

    # THEN
    # we get different option sets in return
    # assert len(cat_dog_auto_data) == 2
    # assert len(cat_dog_fish_auto_data) == 1


def test_auto_data_contains_expected_data():
    # GIVEN
    # preset build from the two different specs
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)
    assert len(auto_data_generator.presets) == 2

    # WHEN
    # we convert values with multiple valid preset specs
    cat_dog_auto_data = auto_data_generator.build_auto_data(['cat', 'dog'])
    cat_dog_fish_auto_data = auto_data_generator.build_auto_data(['cat', 'dog', 'fish'])

    # THEN
    # we get different option sets in return
    assert cat_dog_fish_auto_data[0]['preset']['name'] == 'Fish and Mammals'
    assert cat_dog_fish_auto_data[0]['data'][0] == {'value': 'cat', 'preset': 'Cat', 'standard': 'Cat',
                                                    'parent': 'Mammal', 'order': 2}


def test_preset_maps_different_standard_values_to_same_preset_value():
    # GIVEN
    # preset build from the fish mammal other presets
    preset_data = preset_fish_mammal_other_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)

    # WHEN
    # we auto convert a set with 'reptile' and a set with other
    reptile_auto_data = auto_data_generator.build_auto_data(['mammal', 'fish', 'reptile'])
    other_auto_data = auto_data_generator.build_auto_data(['mammal', 'fish', 'other'])

    # THEN
    # reptile gets mapped to the preset Other value with associated parent and order
    assert reptile_auto_data[0]['data'][2] == {'value': 'reptile', 'standard': 'Reptile',
                                               'preset': 'Other', 'parent': 'Other', 'order': 5}
    # and so does other
    assert other_auto_data[0]['data'][2] == {'value': 'other', 'standard': 'Other',
                                             'preset': 'Other', 'parent': 'Other', 'order': 5}


def test_auto_generator_initialises_from_file():
    # GIVEN
    # the pets data in .csv form
    standardiser_file = 'tests/test_data/test_auto_data/autodata_standardiser.csv'
    preset_file = 'tests/test_data/test_auto_data/autodata_presets.csv'

    # WHEN
    # we initialise a generator
    auto_data_generator = AutoDataGenerator.from_files(standardiser_file, preset_file)

    # THEN
    # we have a valid generator
    assert auto_data_generator is not None
    # that is working as a generator
    cat_dog_fish_auto_data = auto_data_generator.build_auto_data(['feline', 'canine', 'fish'])
    assert cat_dog_fish_auto_data[0]['preset']['name'] == 'Fish and Mammals'
    assert cat_dog_fish_auto_data[0]['data'][0] == {'value': 'feline', 'preset': 'Cat', 'standard': 'Cat',
                                                    'parent': 'Mammal', 'order': 2}
