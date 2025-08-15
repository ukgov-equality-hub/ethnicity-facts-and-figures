import re
import json
import trello
from trello import TrelloClient

from application.cms.service import Service

BOARD_ID = "xgPN2fMa"
TRELLO_LISTS = {
    "67ced83546e9a460b380ccdd": {"name": "Data received", "id": "67ced83546e9a460b380ccdd", "stage": "planned"},

    "67ced83546e9a460b380cce0": {"name": "Data processed by the analyst", "id": "67ced83546e9a460b380cce0", "stage": "progress"},
    "67ced83546e9a460b380ccdb": {"name": "Charts, tables and text created by analyst", "id": "67ced83546e9a460b380ccdb", "stage": "progress"},
    "67ced83546e9a460b380ccde": {"name": "Charts, tables and text created by analyst", "id": "67ced83546e9a460b380ccde", "stage": "progress"},
    "67ced83546e9a460b380ccd4": {"name": "Preparing content", "id": "67ced83546e9a460b380ccd4", "stage": "progress"},
    "67ced83546e9a460b380ccd5": {"name": "Preparing content", "id": "67ced83546e9a460b380ccd5", "stage": "progress"},
    "67ced83546e9a460b380ccd6": {"name": "Quality assurance by senior analyst", "id": "67ced83546e9a460b380ccd6", "stage": "progress"},
    "67ced83546e9a460b380ccda": {"name": "Quality assurance by senior analyst", "id": "67ced83546e9a460b380ccda", "stage": "progress"},
    "67ced83546e9a460b380ccd7": {"name": "Uploading content on EFF", "id": "67ced83546e9a460b380ccd7", "stage": "progress"},
    "67ced83546e9a460b380ccd8": {"name": "Uploading content on EFF", "id": "67ced83546e9a460b380ccd8", "stage": "progress"},

    "67ced83546e9a460b380ccd9": {"name": "Quality assurance by the department", "id": "67ced83546e9a460b380ccd9", "stage": "review"},
    "67ced83546e9a460b380cce3": {"name": "Quality assurance by the department", "id": "67ced83546e9a460b380cce3", "stage": "review"},

    "67ced83546e9a460b380cce2": {"name": "Published", "id": "67ced83546e9a460b380cce2", "stage": "published"},
}

ORGANISATION_LABELS = {
    "CO": "Cabinet Office",
    "DCMS": "Department for Digital, Culture, Media and Sport",
    "DESNZ": "Department for Energy Security and Net Zero",
    "DfE": "Department for Education",
    "DfT": "Department for Transport",
    "DHSC": "Department of Health and Social Care",
    "DWP": "Department for Work and Pensions",
    "HO": "Home Office",
    "MHCLG": "Ministry of Housing, Communities & Local Government",
    "MOD": "Ministry of Defence",
    "MoJ": "Ministry of Justice",
    "Nature England": "Nature England",
    "NHS B&T": "NHS Blood and Transplant",
    "NHS Digital": "NHS Digital",
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
