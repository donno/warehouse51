""""
This makes use of the MTG JSON from http://mtgjson.com/
"""

import argparse
import itertools
import json
import zipfile
import os.path

from reader import Card, Set, parse_lines

class SplitCard:
    # Example
    #1 Integrity // Intervention (GRN) 227
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __getitem__(self, key):
        if key == 'number':
            return os.path.commonprefix([self.a['number'], self.b['number']])
        elif key == 'name':
            return self.a['name'] + ' // ' + self.b['name']
        elif key == 'colorIdentity':
            assert self.a['colorIdentity'] == self.b['colorIdentity']
            return self.a['colorIdentity']
        elif key == 'multiverseId':
            return self.a['multiverseId']
        elif key == 'rarity':
            assert self.a['rarity'] == self.b['rarity']
            return self.a['rarity']
        raise ValueError(key)

    def keys(self):
        return ['number', 'name', 'colorIdentity', 'multiverseId', 'rarity']

    def __getattr__(self, key):
        raise ValueError(key)

class DeckBoxFormat:
    """Formats a collection list into the format used by deckbox.org"""

    """This format uses the name of the set rather than its three letter code."""
    UseSetName = True

    def __init__(self, set_name_from_code):
        """
        set_name_from_code: A callable that maps a set code to its name.
        """
        self.set_name_from_code = set_name_from_code

    def header(self):
        return 'Count,Tradelist Count,Name,Edition,Card Number,Condition,Language,Foil,Signed,Artist Proof,Altered Art,Misprint,Promo,Textless,My Price'

    def format_card(self, count, card, set_code):
        set_name = self.set_name_from_code(set_code)
        assert ',' not in set_name
        if ',' in card['name']:
            name = '"%s"' % card['name']
        else:
            name = card['name']

        name = card['name']
        # The gates have (a) or (b) in their name so remove that.
        if 'gate' in name:
            name = name.replace(' (a)', '').replace(' (b)', '')

        if ',' in name:
            name = '"%s"' % name

        return ','.join([str(count), '0', name, set_name, card['number'], 'Mint', 'English', '', '', '', '','', '', '', ''])


class ScgDeckFormat:
    def format_card(self, count, card, setcode):
        name = card['name']
        return '%d x %s' % (count, name)


class DeckBuilderFormat:
    # I Haven't confirmed if this format is correct.

    def __init__(self, set_name_from_code):
        """
        set_name_from_code: A callable that maps a set code to its name.
        """
        self.set_name_from_code = set_name_from_code

    def header(self):
        return 'Count,Name,Foil,Edition,Condition,Language'

    def format_card(self, count, card, set_code):
        set_name = self.set_name_from_code(set_code)
        line_format = '{count},{name},{foil},{set_name},{condition},{language}'

        name = card['name']
        # The gates have (a) or (b) in their name so remove that.
        if 'gate' in name:
            name = name.replace(' (a)', '').replace(' (b)', '')

        if ',' in name:
            name = '"%s"' % name

        # TODO: look-up set name from the code set_code
        return line_format.format(
            count=count, name=name, set_name=set_name,
            foil='',
            condition='Mint',
            language='English',
            )

class MTGAFormat:
    """Formats a collection list into the format used by MTG Arena."""

    """This format uses the set code rather than its name"""
    UseSetName = False

    @staticmethod
    def format_card(count, card, set_code):
        """Formats as {count} {name} ({set}) {number}"""
        line_format = '{count} {name} ({set}) {number}'
        name = card['name']
        # The gates have (a) or (b) in their name so remove that.
        if 'gate' in name:
            name = name.replace(' (a)', '').replace(' (b)', '')

        return line_format.format(count=count, name=name, set=set_code, number=card['number'])

def load_sets(path):
    with zipfile.ZipFile(path) as myzip:
        with myzip.open('AllSets.json') as reader:
            return json.load(reader)

def cards_by_number(cards):
    for card in cards:
        yield card['number'], card

def format_card(card):
    return json.dumps(card, indent=2)


def load_list(path, sets, expand=True):
    """Loads a list of containing the set code and the card numbers.

    expand: Expand out duplicates (multiples) so the resulting sequence
            contains the duplicates. Otherwise each item will contain the
            number of duplicates instead.
    """

    # TODO: Build as state machine for this. ideally it should keep going
    # until it gets a set code.
    current_set = None
    card_in_set_by_number = {}
    with open(path, 'r') as reader:
        for item in parse_lines(reader, expand):
            if isinstance(item, Set):
                if item.code == 'PRM':
                    print('Skipping promos')
                    continue

                current_set = sets.get(item.code)
                card_in_set_by_number = dict(cards_by_number(current_set['cards']))
                if not current_set:
                    raise ValueError("Invalid set '%s'" % item.code)
            elif current_set and isinstance(item, Card):
                # Card
                try:
                    card = card_in_set_by_number[str(item.number)]

                    # TODO: Split cards are not going to give the right
                    # information.
                    if card["layout"] == "split":
                        card_a = card
                        card_b = card_a.copy()

                        # This isn't quite right as I suspect a number of the properties
                        # for part B are not going to be correct. Like split cards can be
                        # instant on one half and sorcery on the other.
                        card_b['name'] = card_a['names'][1]
                        card = SplitCard(card_a, card_b)
                    else:
                        assert 'multiverseId' in card, 'no multiverse ID for ' + card['name']
                except KeyError:
                    raise KeyError('Could not find %d in %s' % (item.number, current_set['code']))

                if expand:
                    yield current_set['code'], card
                else:
                    yield current_set['code'], item.count, card

format_card_mtga = MTGAFormat.format_card

def format_list(cards, formatter):
    """Formats a list of cards (cards being the JSON objects from the set list)

    At this stage cards are really a tuple of (set_code, count, card)
    """
    output = ''
    if hasattr(formatter, 'header'):
        output += formatter.header() + '\n'
    for set_code, count, card in cards:
        output += formatter.format_card(count, card, set_code) + '\n'
    return output

def merge_cards(cards):
    """Yields a tuple (set code, count, card)"""
    by_number = lambda card: (card[0], int(card[1]['number'].replace('a', '')))
    cards = sorted(cards, key=by_number)
    for _, g in itertools.groupby(list(cards), by_number):
        set_code, card = next(g)
        count = sum(1 for _ in g) + 1
        #if set_code == 'JOU'.lower():
        #    print(set_code, count, card['name'])
        yield set_code, count, card


def convert_draft_decks(format, sets, expand):
    for name in ['first_draft', 'fourth_draft', 'second_draft', 'third_draft', 'red_welcome', 'white_welcome']:
        cards = load_list('../Generated/decks/%s.txt' % name, sets, expand=expand)
        if expand:
            cards = merge_cards(cards)

        with open('../Generated/deckbox_%s.csv' % name, 'w') as writer:
            writer.write(format_list(cards, format))

def argument_parser():
    """Return an argument parser for processing this."""
    parser = argparse.ArgumentParser(description='Read a set code and numerical card list for MTG.')
    parser.add_argument('--sets', dest='sets_filename', action='store',
                        default='MTG_AllSets.json.zip',
                        help='the file to sets file from http://mtgjson.com/')
    parser.add_argument('card_lists', metavar='CARDLIST', nargs='*',
                        default=['../Real Decks/COLLECTION.txt'],
                        help='the file(s) that contains the owned card list(s).')
    return parser

if __name__ == '__main__':
    parser = argument_parser()
    args = parser.parse_args()

    sets = load_sets(args.sets_filename)
    m19_by_number = dict(cards_by_number(sets['M19']['cards']))

    set_name_from_code = lambda code: sets[code.upper()]['name']

    #print(json.dumps(sets['M19']['cards'][0], indent=2))
    #print(format_card(m19_by_number['32']))

    expand = True

    cards = load_list(args.card_lists[0], sets, expand=expand)

    if expand:
        cards = merge_cards(cards)

    cards = list(cards)
    #print(cards[0][2])

    deckbox = DeckBoxFormat(set_name_from_code)
    deckbuilder = DeckBuilderFormat(set_name_from_code)
    mtga = MTGAFormat()
    scg = ScgDeckFormat()

    deckformat = mtga
    print(format_list(cards, deckformat))

    with open('../Generated/scg_collection_temp2.txt.csv', 'w') as writer:
        writer.write(format_list(cards, scg))

    #convert_draft_decks(deckbox, sets, expand=True)
