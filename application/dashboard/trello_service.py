import re
import json
import trello
from trello import TrelloClient

from application.cms.service import Service

BOARD_ID = "K3A3MP7x"
TRELLO_LISTS = {
    "5a686d4076c5194520f1186c": {"name": "Planned", "id": "5a686d4076c5194520f1186c", "stage": "planned"},
    "5b90ec017b538e7de152dbc0": {"name": "Data received", "id": "5b90ec017b538e7de152dbc0", "stage": "planned"},
    "5cc705f5771ebd73cb216caa": {"name": "Departmental updates", "id": "5cc705f5771ebd73cb216caa", "stage": "planned"},
    "5b90ec070793305d06d2b01f": {
        "name": "Data checks in progress",
        "id": "5b90ec070793305d06d2b01f",
        "stage": "progress",
    },
    "5a686ce113786b932cf745b4": {
        "name": "Content design backlog",
        "id": "5a686ce113786b932cf745b4",
        "stage": "progress",
    },
    "5a686ce113786b932cf745b5": {
        "name": "Content design in progress",
        "id": "5a686ce113786b932cf745b5",
        "stage": "progress",
    },
    "5a686ce113786b932cf745b6": {
        "name": "Needs senior analyst sign off",
        "id": "5a686ce113786b932cf745b6",
        "stage": "progress",
    },
    "5a686ce113786b932cf745b7": {"name": "Ready for upload", "id": "5a686ce113786b932cf745b7", "stage": "progress"},
    "5a686ce113786b932cf745b8": {"name": "Uploaded", "id": "5a686ce113786b932cf745b8", "stage": "progress"},
    "5a686ce113786b932cf745ba": {"name": "Department review", "id": "5a686ce113786b932cf745ba", "stage": "review"},
    "5a686ce113786b932cf745bd": {"name": "Published", "id": "5a686ce113786b932cf745bd", "stage": "published"},
    "5a686fb201a2b230f9de88cd": {"name": "Not being worked on", "id": "5a686fb201a2b230f9de88cd", "stage": "other"},
}

TYPE_OF_WORK_LABELS = {
    "New measure": "New measure",
    "Updated version": "Updated version",
    "Updated version v3": "Updated version",
}

ORGANISATION_LABELS = {
    "BEIS": "Department for Business, Energy & Industrial Strategy",
    "CO": "Cabinet Office",
    "DCMS": "Department for Digital, Culture, Media and Sport",
    "DEFRA": "Department for Environment, Food & Rural Affairs",
    "DfE": "Department for Education",
    "DfT": "Department for Transport",
    "DHSC": "Department of Health and Social Care",
    "DWP": "Department for Work and Pensions",
    "HESA": "Higher Education Statistics Agency",
    "HO": "Home Office",
    "MHCLG": "Ministry of Housing, Communities & Local Government",
    "MOD": "Ministry of Defence",
    "MoJ": "Ministry of Justice",
    "ONS": "Office for National Statistics",
}


# "What is this method doing here?", you may ask:
# Trello have made this change: https://developer.atlassian.com/changelog/#CHANGE-1459 ("Trello API will no longer accept GET request with data in body")
# The Trello API client we're using (py-trello) hasn't been updated to work with this change
# An issue has been raised, but not yet fixed, but there is a suggested work-around: https://github.com/sarumont/py-trello/issues/373#issuecomment-1958814294
def patched_fetch_json(self,
                       uri_path,
                       http_method='GET',
                       headers=None,
                       query_params=None,
                       post_args=None,
                       files=None):
    """ Fetch some JSON from Trello """

    # explicit values here to avoid mutable default values
    if headers is None:
        headers = {}
    if query_params is None:
        query_params = {}
    if post_args is None:
        post_args = {}

    # if files specified, we don't want any data
    data = None
    if files is None and post_args != {}:
        data = json.dumps(post_args)

    # set content type and accept headers to handle JSON
    if http_method in ("POST", "PUT", "DELETE") and not files:
        headers['Content-Type'] = 'application/json; charset=utf-8'

    headers['Accept'] = 'application/json'

    # construct the full URL without query parameters
    if uri_path[0] == '/':
        uri_path = uri_path[1:]
    url = 'https://api.trello.com/1/%s' % uri_path

    if self.oauth is None:
        query_params['key'] = self.api_key
        query_params['token'] = self.api_secret

    # perform the HTTP requests, if possible uses OAuth authentication
    response = self.http_service.request(http_method, url, params=query_params,
                                         headers=headers, data=data,
                                         auth=self.oauth, files=files,
                                         proxies=self.proxies)

    if response.status_code == 401:
        raise trello.Unauthorized("%s at %s" % (response.text, url), response)
    if response.status_code != 200:
        raise trello.ResourceUnavailable("%s at %s" % (response.text, url), response)

    return response.json()


trello.TrelloClient.fetch_json = patched_fetch_json


class TrelloService(Service):
    api_key = ""
    api_token = ""
    client = None

    # Matches a leading reference number in square brackets plus optional space
    # e.g. for "[BLAH 002] New measure name" this will match the "[BLAH 002] " at the start
    INTERNAL_REFERENCE_REGEX = re.compile(r"^\[.+?\]\s*")

    def is_initialised(self):
        return self.api_key != "" and self.api_token != ""

    def set_credentials(self, api_key, api_token):

        self.api_key = api_key
        self.api_token = api_token
        self.client = TrelloClient(api_key=api_key, api_secret=api_token)

    def get_measure_cards(self):
        cards = [card for card in self.client.get_board(BOARD_ID).all_cards() if card.closed is False]

        card_dicts = [self._map_card(card) for card in cards]
        card_dicts = [card_dict for card_dict in card_dicts if card_dict["department"] and card_dict["stage"]]

        return card_dicts

    def _map_card(self, card):
        obj = {
            "id": card.id,
            "name": self._remove_internal_reference(card.name),
            "department": self._find_label_from_card(card, ORGANISATION_LABELS),
            "type": self._find_label_from_card(card, TYPE_OF_WORK_LABELS),
            "list": "",
            "stage": "",
        }
        if card.idList in TRELLO_LISTS:
            obj["list"] = TRELLO_LISTS[card.idList]["name"]
            obj["stage"] = TRELLO_LISTS[card.idList]["stage"]
        return obj

    @staticmethod
    def _find_label_from_card(card, label_lookup_dict):
        if card.labels:
            for label in card.labels:
                if label.name in label_lookup_dict:
                    return label_lookup_dict[label.name]
        return ""

    @staticmethod
    def _remove_internal_reference(card_name):
        return re.sub(TrelloService.INTERNAL_REFERENCE_REGEX, "", card_name)


trello_service = TrelloService()
