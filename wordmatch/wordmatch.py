"""Match a bunch of jumbled letters with words.

This particular module provides functions for working with "Word Mastermind".
The idea is a word is selected and the player makes guesses for what the word
is. The following information is received upon making a guess:
- Which letters do not appear
- Which letters do appear but are in the wrong position
- Which letters do appear and are in the right position.
"""

# NAME         : WordMatch
# SUMMARY      : Match a bunch of jumbled letters with words.
# COPYRIGHT    : (c) 2022 Sean Donnellan. All Rights Reserved.
# LICENSE      : The MIT License (see LICENSE.txt for details)

import collections
import unittest


__version__ = '0.2.0'
__copyright__ = "Copyright 2022, https://github.com/donno/"


class WordList:
    def __init__(self, path):
        with open(path, 'rb') as reader:
            # Read the first 8-bytes which is the length.
            self._length = int.from_bytes(reader.read(8), byteorder='little')
            self.contents = reader.read()

    @property
    def word_length(self):
        """The length of each word. A word list always contains the same
        length words."""
        return self._length

    def __len__(self):
        """The number of words in the list."""
        return len(self.contents) // (self.word_length * 2 + 2)

    def __getitem__(self, index):
        """The word at the given index."""
        if index >= len(self):
            raise IndexError(f'Given index of {index} out of {len(self)}')

        start = self._entry_offset(index) + self.word_length
        word = self.contents[start:start + self.word_length]
        return word.decode('utf-8')

    # TODO: Provide a version of iter which gives the values.
    # TODO: Provide a keys(), values() and items() view.

    def key(self, index):
        """The key is simply the letters in the word sorted."""
        start = self._entry_offset(index)
        return self.contents[start:start + self.word_length].decode('utf-8')

    def _entry_offset(self, index):
        """Given the index of an entry (i.e the entry number) return the offset
        to the entry in the byte array (contents).
        """

        # An entry is the key followed by word, a null terminator for the word
        # and a new line.
        #
        # The null-terminator makes it easier for C & C++ to print out the
        # word and the new line makes it easier to view the resulting file
        # in a text editor.
        entry_length = self.word_length * 2 + 2
        return index * entry_length


def filter(positional, exists):
    def _filter(word):
        assert len(word) == len(positional), (word, positional)

        word = word.upper()

        # For each non-None element in positional check that it exists in word
        positional_matches = all(
            position is None or position == letter
            for position, letter in zip(positional, word)
        )

        if not positional_matches:
            return False

        exists_matches = all(letter in word for letter in exists)
        return exists_matches

    return _filter


def filter_misses(positional_misses, does_not_exists):
    """Filters out words that uses letters that are known not to exist in the
    word.

    positional_misses: List of letters for each position that shouldn't be at
                       that position but should exist in the word.
    does_not_exists: List of letters that don't appear anywhere.
    """
    def _filter(word):
        assert len(word) == len(positional_misses), (word, positional_misses)
        word = word.upper()

        positional_matches = any(
            letter in (position or '')
            for position, letter in zip(positional_misses, word)
        )

        if positional_matches:
            return False

        return not any(letter in word for letter in does_not_exists)

    return _filter


def filtered_words(words: WordList, *filters):
    return [word for word in words
            if all(matcher(word) for matcher in filters)]


class FilterTest(unittest.TestCase):
    """Tests for the filter() function."""
    def test_positional_positives(self):
        matches = filter([None, None, 'I', None, None], '')
        self.assertTrue(matches('QUILL'))
        self.assertTrue(matches('UNIFY'))
        self.assertTrue(matches('TWIST'))
        self.assertTrue(matches('SPITS'))

    def test_positional_negatives(self):
        matches = filter([None, None, 'I', None, None], '')
        self.assertFalse(matches('WATER'))
        self.assertFalse(matches('BOUGH'))

    def test_exists_positives(self):
        matches = filter([None, None, None, None, None], 'U')
        self.assertTrue(matches('QUILL'))
        self.assertTrue(matches('UNIFY'))
        self.assertTrue(matches('BOUGH'))

    def test_exists_negatives(self):
        matches = filter([None, None, None, None, None], 'U')
        self.assertFalse(matches('WATER'))

    def test_both_positives(self):
        matches = filter([None, None, 'I', None, None], 'U')
        self.assertTrue(matches('QUILL'))
        self.assertTrue(matches('UNIFY'))

    def test_both_negatives(self):
        matches = filter([None, None, 'I', None, None], 'U')

        # Nothing matches
        self.assertFalse(matches('WATER'))

        # Exists matches but positional doesn't.
        self.assertFalse(matches('TRUST'))
        self.assertFalse(matches('TUTTY'))
        self.assertFalse(matches('tutty'))

        # Positional matches but exists doesn't.
        self.assertFalse(matches('TWIST'))
        pass # TODO

class FilterMissesTest(unittest.TestCase):
    """Tests for the filter_misses() function."""

    def test_letters_missing(self):
        matches = filter_misses([None] * 5, 'AERTW')
        self.assertFalse(matches('WATER'))

    def test_letters_positional(self):
        matches = filter_misses(['', '', 'U', '', ''], 'AERTW')
        self.assertFalse(matches('WATER'))
        self.assertFalse(matches('BOUGH'))

        matches = filter_misses([None, None, 'U', None, None], 'AERTW')
        self.assertFalse(matches('WATER'))
        self.assertFalse(matches('BOUGH'))


def steps():
    words = WordList('data/wordlist5.bin')

    # First attempt: "WATER"
    matches = filter([None] * 5, '')
    missing_matches = filter_misses([None] * 5, 'WATER')
    candidates = filtered_words(words, matches, missing_matches)
    print('Candidates after attempt 1:', len(candidates))

    # Second attempt: "BOUGH"
    matches = filter([None, None, None, None, None], 'U')
    missing_matches = filter_misses([None, None, 'U', None, None], 'WATERBOGH')
    candidates = filtered_words(words, matches, missing_matches)
    print('Candidates after attempt 2:', len(candidates))

    # Third attempt: "QUILL"
    matches = filter([None, None, 'I', None, None], 'U')
    missing_matches = filter_misses([None, 'U', 'U', None, None],
                                    'WATERBOGHQL')
    candidates = filtered_words(words, matches, missing_matches)
    print('Candidates after attempt 3:', len(candidates))
    print(candidates)


def choose_best_word(words: WordList):
    def _letters_in_words(words):
        for word in words:
            yield from word

    letter_frequency = collections.Counter(_letters_in_words(words))
    common_letters = dict(letter_frequency.most_common(10))

    matches = lambda word: any(letter in common_letters for letter in word)
    always_true = lambda word: True


    def by_common_letter(word):
        # Ignore doubles or triples of the same letter as that hurts the
        # chances of eliminating the most letters at once. This is achieved by
        # converting the word to a set.
        return sum(common_letters[letter] for letter in set(word)
                   if letter in common_letters)

    candidates = filtered_words(words, matches, always_true)

    # Rank the words based on if they in the top 10 most common.
    return sorted(candidates, key=by_common_letter)[-5:]


def filter_words_with_duplicates(word):
    return len(set(word)) == len(word)


if __name__ == '__main__':
    #unittest.main()
    #steps()
    words = WordList('data/wordlist5.bin')
    choose_best_word(words)

    # AROSE
    #
    # Results: RSE exist but not in those positions.
    matches = filter([None] * 5, 'RSE')
    missing_matches = filter_misses(['', 'R', '', 'S', 'E'], 'AO')
    candidates = filtered_words(words, matches, missing_matches,
                                filter_words_with_duplicates)
    #print(f'Candidates: {len(candidates)}')
    #print('\n'.join(candidates))
    # "RULES"
    matches = filter(['R', None, None, None, 'S'], 'RUES')
    missing_matches = filter_misses(['', 'RU', '', 'SE', 'E'], 'AOL')
    candidates = filtered_words(words, matches, missing_matches,
                                filter_words_with_duplicates)
    if not candidates:
        candidates = filtered_words(words, matches, missing_matches)

    print(f'Candidates: {len(candidates)}')
    print('\n'.join(candidates))
