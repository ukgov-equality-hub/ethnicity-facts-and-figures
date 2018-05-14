from trello import TrelloClient

from application.cms.service import Service

BOARD_ID = 'K3A3MP7x'
TRELLO_LISTS = {
    '5a686d4076c5194520f1186c': {'name': 'Planned', 'id': '5a686d4076c5194520f1186c', 'stage': 'planned'},
    '5a686ce113786b932cf745b2': {'name': 'Received, In progress', 'id': '5a686ce113786b932cf745b2',
                                 'stage': 'progress'},
    '5a686ce113786b932cf745b4': {'name': 'Content design backlog', 'id': '5a686ce113786b932cf745b4',
                                 'stage': 'progress'},
    '5a686ce113786b932cf745b5': {'name': 'Content design in progress', 'id': '5a686ce113786b932cf745b5',
                                 'stage': 'progress'},
    '5a686ce113786b932cf745b6': {'name': 'Needs senior analyst sign off', 'id': '5a686ce113786b932cf745b6',
                                 'stage': 'progress'},
    '5a686ce113786b932cf745b7': {'name': 'Ready for upload', 'id': '5a686ce113786b932cf745b7', 'stage': 'progress'},
    '5a686ce113786b932cf745b8': {'name': 'Uploaded', 'id': '5a686ce113786b932cf745b8', 'stage': 'progress'},
    '5a686ce113786b932cf745ba': {'name': 'Department review', 'id': '5a686ce113786b932cf745ba', 'stage': 'review'},
    '5a686ce113786b932cf745bd': {'name': 'Published', 'id': '5a686ce113786b932cf745bd', 'stage': 'published'},
    '5a686fb201a2b230f9de88cd': {'name': 'Not being worked on', 'id': '5a686fb201a2b230f9de88cd', 'stage': 'other'}
}

WORK_FLAGS = ('New measure', 'Updated version')
DEPARTMENT_FLAGS = ('BEIS', 'CO', 'DCMS', 'MHCLG', 'DEFRA', 'DfE', 'DfT', 'DH', 'DWP', 'HO', 'MoJ', 'ONS', 'RDU',
                    'MOD')


class TrelloService(Service):
    api_key = ''
    api_token = ''
    client = None

    def is_initialised(self):
        return self.api_key != '' and self.api_token != ''

    def set_credentials(self, api_key, api_token):

        self.api_key = api_key
        self.api_token = api_token
        self.client = TrelloClient(
            api_key=api_key,
            api_secret=api_token
        )

    def get_measure_cards(self):
        cards = [card for card in self.client.get_board(BOARD_ID).all_cards() if card.closed is False]

        card_dicts = [self.map_card(card) for card in cards]
        card_dicts = [card_dict for card_dict in card_dicts if
                      card_dict['department'] and card_dict['stage']]

        return card_dicts

    def map_card(self, card):
        obj = {
            'id': card.id,
            'name': card.name,
            'department': self.find_flag(card, DEPARTMENT_FLAGS),
            'type': self.find_flag(card, WORK_FLAGS),
            'list': '', 'stage': ''
        }
        if card.idList in TRELLO_LISTS:
            obj['list'] = TRELLO_LISTS[card.idList]['name']
            obj['stage'] = TRELLO_LISTS[card.idList]['stage']
        return obj

    def find_flag(self, card, flags):
        for flag in card.labels:
            if flag.name in flags:
                return flag.name
        return ''


trello_service = TrelloService()
