"""
AutoDataGenerator

AutoDataGenerator turns a list of ethnicity values from departments into standard list of ethnicities
alongside parent groups and the orders they should be displayed.

It may be that values can be encoded in several different ways so AutoDataGenerator has the concept of presets.

When you call `build_auto_data(values)` it checks whether `values` can be encoded using each preset and returns a list
of all valid presets with the encoded data

"""

from application.cms.data_utils import AutoDataGenerator


def test_preset_service_does_initialise():
    preset_service = AutoDataGenerator(standardiser_lookup=[], preset_lookup=[])

    assert preset_service is not None


def test_preset_service_does_initialise_with_simple_values():
    # GIVEN
    # some simple data
    standardiser_data = [['alpha', 'Alpha'], ['aleph', 'Alpha']]
    preset_data = [['alpha', 'a', 'a', '', 0], ['alpha', 'b', 'b', '', 1],
                   ['beta', 'a', 'a', '', 0], ['beta', 'b', 'b', '', 1]]

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
    return [['Cats and Dogs', 'Cat', 'Cat', 'Cat', 1],
            ['Cats and Dogs', 'Dog', 'Dog', 'Dog', 2]]


def preset_fish_and_mammal_parent_child_data():
    return [
        ['Fish and Mammals', 'Mammal', 'Mammal', 'Mammal', 1],
        ['Fish and Mammals', 'Cat', 'Cat', 'Mammal', 2],
        ['Fish and Mammals', 'Dog', 'Dog', 'Mammal', 3],
        ['Fish and Mammals', 'Fish', 'Fish', 'Fish', 4],
    ]


def preset_fish_mammal_other_data():
    return [
        ['Fish, Mammal, Other', 'Mammal', 'Mammal', 'Mammal', 1],
        ['Fish, Mammal, Other', 'Cat', 'Cat', 'Mammal', 2],
        ['Fish, Mammal, Other', 'Dog', 'Dog', 'Mammal', 3],
        ['Fish, Mammal, Other', 'Fish', 'Fish', 'Fish', 4],
        ['Fish, Mammal, Other', 'Other', 'Other', 'Other', 5],
        ['Fish, Mammal, Other', 'Reptile', 'Other', 'Other', 5]
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


def test_standardiser_does_convert_unknown_value_to_none():
    # GIVEN
    # the pet standardiser
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_cats_and_dogs_data())

    # WHEN
    # standardiser converts a value that is not present
    actual = ['cathedral']
    converted = auto_data_generator.convert_to_standard_data(actual)

    # THEN
    # the value is the expected one
    expected = [{'value': 'cathedral', 'standard': None}]
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
    # preset build from the Cats and Dogs spec
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)

    # WHEN
    # we validate it against the values Cat, Dog and Fish
    cat_dog_fish_valid_presets = auto_data_generator.get_valid_presets_for_data(['Cat', 'Dog', 'Fish'])
    cat_dog_valid_presets = auto_data_generator.get_valid_presets_for_data(['Cat', 'Dog'])
    cat_velociraptor_valid_presets = auto_data_generator.get_valid_presets_for_data(['Cat', 'Velociraptor'])

    # THEN
    # the validation is correct
    assert len(cat_dog_fish_valid_presets) == 1
    assert len(cat_dog_valid_presets) == 2
    assert len(cat_velociraptor_valid_presets) == 0


def test_multiple_presets_exclude_invalid_ones():
    # GIVEN
    # preset build from the two different specs
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)
    assert len(auto_data_generator.presets) == 2

    # WHEN
    # we validate it against the values Cat, Dog and Fish
    cat_dog_fish_valid_presets = auto_data_generator.get_valid_presets_for_data(['Cat', 'Dog', 'Fish'])

    # THEN
    # we expect only the fish and mammals preset to be valid
    assert len(cat_dog_fish_valid_presets) == 1


def test_multiple_presets_include_all_valid_ones():
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
    assert len(cat_dog_valid_presets) == 2


def test_build_auto_data_returns_set_of_auto_data_for_each_valid_preset():
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
    assert len(cat_dog_auto_data) == 2
    assert len(cat_dog_fish_auto_data) == 1


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
    reptile_auto_data = auto_data_generator.build_auto_data(['reptile'])
    other_auto_data = auto_data_generator.build_auto_data(['other'])

    # THEN
    # reptile gets mapped to the preset Other value with associated parent and order
    assert reptile_auto_data[0]['data'][0] == {'value': 'reptile', 'standard': 'Reptile',
                                               'preset': 'Other', 'parent': 'Other', 'order': 5}
    # and so does other
    assert other_auto_data[0]['data'][0] == {'value': 'other', 'standard': 'Other',
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
