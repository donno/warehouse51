#ifndef WORDMATCH_WORD_LIST_H
#define WORDMATCH_WORD_LIST_H
//===----------------------------------------------------------------------===//
//
// NAME         : WordList
// SUMMARY      : Provides an list of words of a certain length.
// COPYRIGHT    : (c) 2014 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
// DESCRIPTION  : The word list is stored in a stored format to allow for
//                O(log N) look-up of words with a given set of letters.
//
//===----------------------------------------------------------------------===//

#include <iosfwd>
#include <memory>
#include <string>
#include <utility>

class WordListIterator;

class WordList
{
  typedef char word_type;

  // The storage for the words.
  std::unique_ptr<word_type[]> words;

  // The total number of characters in words (i.e across all words).
  std::size_t size;

  // The length of each word.
  std::size_t length;

public:
  WordList(std::ifstream& input, std::size_t inputSize);

  WordListIterator begin() const;
  WordListIterator end() const;

  // Returns matches for the word for [begin, end) which match word.
  std::pair<WordListIterator, WordListIterator> matches(std::string word) const;

  // Sort the words. This is used when the original word list was not sorted and
  // so doesn't need to be called if reading an existing word list binary.
  void sort();

  // Write the existing word list out to a file stream.
  void write(std::ofstream& output) const;

  friend class WordListIterator;
};

#endif
