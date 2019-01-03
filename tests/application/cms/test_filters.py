import pytest

from application.cms.filters import index_of_last_initial_zero, yesno


class TestYesNo:
    @pytest.mark.parametrize(
        "input_value, expected_output",
        ((True, "yes"), (False, "no"), (1, 1), (0, 0), ("true", "true"), ("false", "false"), ("abc", "abc")),
    )
    def test_yesno_converts_boolean_true_and_false_only(self, input_value, expected_output):
        assert yesno(input_value) == expected_output


class TestIndexOfLastInitialZero:
    def test_when_only_one_zero(self):
        assert index_of_last_initial_zero([0, 10, 20]) == 0

    def test_when_many_zeros(self):
        assert index_of_last_initial_zero([0, 0, 0, 0, 1, 2]) == 3

    def test_when_later_zeros_are_present(self):
        assert index_of_last_initial_zero([0, 0, 1, 2, 1, 0]) == 1

    def test_when_no_zeros_are_present(self):
        with pytest.raises(ValueError):
            index_of_last_initial_zero([1, 2, 3, 4])

    def test_when_array_contains_strings(self):
        with pytest.raises(ValueError):
            index_of_last_initial_zero(["0", "1", "2"])
