'''
Ethnicity presets will allow us to customise our chart and table builders for Ethnicity Facts and Figures

By using a preset we can go straight from the ethnicities in a data set through to having Standard Ethnicity, Parent, and Order

Language

'''
from application.cms.data_utils import AutoDataGenerator


def test_preset_service_does_initialise():
    preset_service = AutoDataGenerator(standardiser_lookup=[], preset_lookup=[])

    assert preset_service is not None


def test_preset_service_does_initialise_with_simple_values():
    # GIVEN
    # some simple data
    standardiser_data = [['alpha', 'Alpha'], ['aleph', 'Alpha']]
    preset_data = [['alpha', 'a', '', 0], ['alpha', 'b', '', 1],
                   ['beta', 'a', '', 0], ['beta', 'b', '', 1]]

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
    ]


def preset_cats_and_dogs_data():
    return [['Cats and Dogs', 'Cat', 'Cat', 1],
            ['Cats and Dogs', 'Dog', 'Dog', 2]]


def preset_fish_and_mammal_parent_child_data():
    return [
        ['Fish and Mammals', 'Mammal', 'Mammal', 1],
        ['Fish and Mammals', 'Cat', 'Mammal', 2],
        ['Fish and Mammals', 'Dog', 'Mammal', 3],
        ['Fish and Mammals', 'Fish', 'Fish', 4],
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


def test_build_auto_data_returns_set_of_options_for_each_valid_preset():
    # GIVEN
    # preset build from the two different specs
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)
    assert len(auto_data_generator.presets) == 2

    # WHEN
    # we convert values with multiple valid preset specs
    cat_dog_options = auto_data_generator.build_auto_data(['cat', 'dog'])
    cat_dog_fish_options = auto_data_generator.build_auto_data(['cat', 'dog', 'fish'])

    # THEN
    # we get different option sets in return
    assert len(cat_dog_options) == 2
    assert len(cat_dog_fish_options) == 1


def test_auto_data_contains_expected_data():
    # GIVEN
    # preset build from the two different specs
    preset_data = preset_cats_and_dogs_data() + preset_fish_and_mammal_parent_child_data()
    auto_data_generator = AutoDataGenerator(pet_standards(), preset_data)
    assert len(auto_data_generator.presets) == 2

    # WHEN
    # we convert values with multiple valid preset specs
    cat_dog_options = auto_data_generator.build_auto_data(['cat', 'dog'])
    cat_dog_fish_options = auto_data_generator.build_auto_data(['cat', 'dog', 'fish'])

    # THEN
    # we get different option sets in return
    assert cat_dog_fish_options[0]['preset']['name'] == 'Fish and Mammals'
    assert cat_dog_fish_options[0]['data'][0] == {'value': 'cat', 'standard': 'Cat', 'parent': 'Mammal', 'order': 2}
