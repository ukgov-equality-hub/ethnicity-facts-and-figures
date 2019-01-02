import pytest
from unittest import mock

from application.dashboard.trello_service import trello_service


# Mock out the Trello client at class level to be sure we don't make any calls out to external Trello API
@mock.patch.object(trello_service, "client")
class TestTrelloService:
    def test_client_is_mocked(self, client):
        trello_service.get_measure_cards()
        client.get_board.assert_called_with(mock.ANY)

    @pytest.mark.parametrize(
        "card_name, expected_output",
        (
            ("Just a title", "Just a title"),
            ("[ABC 123] Here's a title", "Here's a title"),
            ("[AB[C[[ 123] Here's a title", "Here's a title"),
            ("[ABC 123] [Here's] a title", "[Here's] a title"),
            ("[ABC []123] Here's a title", "123] Here's a title"),
            ("]ABC 123[ Here's a title", "]ABC 123[ Here's a title"),
            ("Something first [ABC 123] Here's a title", "Something first [ABC 123] Here's a title"),
            ("Ref not last [ABC 123]", "Ref not last [ABC 123]"),
        ),
    )
    def test_removal_of_internal_reference(self, client, card_name, expected_output):
        assert trello_service._remove_internal_reference(card_name) == expected_output
