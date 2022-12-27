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
    return sorted([word for word in words
            if all(matcher(word) for matcher in filters)])


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


class MatchWord:
    """Implement a game where a word is chosen and the player must take guesses
    at the word.
    """

    class GuessCountExceededError(ValueError):
        def __init__(self):
            super().__init__('Too many guesses were taken.')


    class GuessResult:
        """
        The encoded result works as follows if the target is:
            WATER
        The first guess is:
            AROSE
        Then for each letter in the guess that is not in the target will have
        a 0, each letter in the guess that is in the right position will have a
        1 and 2 otherwise (i.e letters in the target but in the wrong space).
        """

        def __init__(self, encoded_result: str):
            self.encoded_result = encoded_result

        def __eq__(self, other: object) -> bool:
            other_encoded_result = getattr(other, 'encoded_result', None)
            if other_encoded_result:
                return self.encoded_result == other_encoded_result
            return self.encoded_result == other

        def __repr__(self):
            return f'GuessResult({self.encoded_result})'

        @property
        def count_correct_letter_and_position(self):
            return self.encoded_result.count('1')

        @property
        def count_correct_letter_and_wrong_position(self):
            return self.encoded_result.count('2')

    # TODO: Add validation to ensure target and any guesses are valid works
    # based on a dictionary.

    def __init__(self, target):
        if len(target) != 5:
            raise ValueError('Target word must be at 5 characters long.')

        self.target = target
        self.guess_number = 0

    def guess(self, word):
        # The target word length is known information and thus is something
        # that the caller can know for free.
        target_length = len(self.target)
        if len(word) != target_length:
            raise ValueError(
                f'Target word is {target_length} characters long. The guess '
                f'had only {len(word)}')

        target = self.target.upper()
        word = word.upper()

        if target == word:
            return self.GuessResult('1' * target_length), True

        def classify(letter_target, letter_guess):
            if letter_target == letter_guess:
                return '1'

            if letter_guess not in target:
                return '0'

            return '?'

        # First pass - find exact matches and complete misses.
        encoded_result = [classify(a, b) for a, b in zip(target, word)]

        # Second pass - resolve ? to 2 or to a 0 if it was a double letter.
        #
        # If the guess was "floor" but the target was flour we don't want to
        # say the second o is is simply in the wrong position.
        remaining_letters = {
            letter for letter, r in zip(target, encoded_result)
            if r != '1'
        }

        def classify_wrong_spot(letter_guess, encoded):
            if encoded == '?':
                if letter_guess in remaining_letters:
                    remaining_letters.remove(letter_guess)
                    return '2'
                else:
                    return '0'

            return encoded

        encoded_result = [
            classify_wrong_spot(letter_guess, encoded)
            for letter_guess, encoded in zip(word, encoded_result)
        ]

        self.guess_number += 1

        if self.guess_number == 6:
            raise self.GuessCountExceededError()

        return self.GuessResult(''.join(encoded_result)), False


class MatchWordTest(unittest.TestCase):
    def test_validate_target_length(self):
        with self.assertRaises(ValueError):
            MatchWord('a')

        with self.assertRaises(ValueError):
            MatchWord('abc')

        with self.assertRaises(ValueError):
            MatchWord('abcdefghji')

        MatchWord('abcde')  # Expected length is 5.

    def test_validate_guess_length(self):
        game = MatchWord('abcde')
        with self.assertRaises(ValueError):
            game.guess('a')

        with self.assertRaises(ValueError):
            game.guess('abc')

        with self.assertRaises(ValueError):
            game.guess('abcdefghji')

        game.guess('abcde')

    def test_first_guess_right(self):
        game = MatchWord('WATER')
        game.guess('WATER')

    def test_first_guess_miss(self):
        game = MatchWord('WATER')
        result = game.guess('AROSE')
        self.assertEqual(result, '22002')

    def test_guess_duplicates(self):
        """Duplicate letter shouldn't be counted as misses twice."""
        game = MatchWord('FLOUR')
        result = game.guess('FLOOR')
        self.assertNotEqual(result, '11121')
        self.assertEqual(result, '11101')

    def test_too_many_guesses(self):
        game = MatchWord('WATER')
        for _ in range(0, 5):
            game.guess('AROSE')

        with self.assertRaises(MatchWord.GuessCountExceededError):
            game.guess('AROSE')


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


def letters_in_words(words):
    """Yield each letter in the words.

    This is useful for passing to a collection.Counter()"""
    for word in words:
        yield from word


def determine_required_letters_from_words(words: list):
    """Determine what letters must be required in the word based on checking
    what letters existing in all of the given words.

    words must not contain words with duplicate letters as this algorithm
    doesn't handle that."""


    # Letters where the count = len(candidates_without_dupes) are the required
    # letters.
    counter = collections.Counter(letters_in_words(words))
    required_letters = [letter for letter, count in counter.items()
                        if count == len(words)]
    return required_letters

def report(words: WordList, matches, missing_matches,
           with_untried_summary=False):
    candidates_with_dupes = filtered_words(words, matches, missing_matches)
    candidates_without_dupes = filtered_words(
        candidates_with_dupes, filter_words_with_duplicates)

    if candidates_without_dupes:
        print(f'candidates (no duplicates)')
        print('  ' + '\n  '.join(candidates_without_dupes))
        if len(candidates_without_dupes) < 5:
            print('candidates (with duplicates)')
            print('  ' + '\n  '.join(candidates_with_dupes))
    else:
        print('candidates (with duplicates)')
        print('  ' + '\n  '.join(candidates_with_dupes))

    def remove_letters(word, required_letters):
        return ''.join(letter for letter in word
                       if letter not in required_letters)

    # As the filters are transparent what letters are required needs to be
    # deduced. These letters should appear in every candindate.
    required_letters = determine_required_letters_from_words(
        candidates_without_dupes)

    print(required_letters)
    candindates_without_required_letters = [
        remove_letters(word, required_letters)
        for word in candidates_without_dupes
        ]

    if with_untried_summary:
        untried_letters = collections.Counter(
            letters_in_words(candindates_without_required_letters))

        print('Untried letters in candidates')
        print('  ' + '\n  '.join(
                f'{v} {k}' for k, v in untried_letters.most_common(28)))
        print('Find words with the most common set of letters')


def jan3(words: WordList):
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


def jan4(words: WordList):
    print('Initial candindates')
    print('  ' + '\n  '.join(choose_best_word(words)))

    # AROSE
    #
    # Results: OS exist and is in those position everything else was a miss.
    matches = filter([None, None, 'O', 'S', None], '')
    missing_matches = filter_misses(['', '', '', '', ''], 'ARE')
    print('> After 1st guess')
    report(words, matches, missing_matches)

    # Ghost (This time the fact I filtered duplicated was bad as it was
    # duplicate)
    matches = filter([None, None, 'O', 'S', 'T'], '')
    missing_matches = filter_misses(['', '', '', '', ''], 'GHARE')
    print('> After 2nd guess')
    report(words, matches, missing_matches)


if __name__ == '__main__':
    #unittest.main()
    #steps()
    words = WordList('data/wordlist5.bin')
    jan4(words)
