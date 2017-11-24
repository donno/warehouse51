#ifndef WORDMATCH_WORD_LIST_ITERATOR_H
#define WORDMATCH_WORD_LIST_ITERATOR_H
//===----------------------------------------------------------------------===//
//
// NAME         : WordListIterator
// SUMMARY      : Provides an random access iterator over the WordList.
// COPYRIGHT    : (c) 2014 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
//
//===----------------------------------------------------------------------===//

#include <iterator>

#ifdef _MSC_VER
#pragma warning(disable: 4510)    // default constructor could not be generated
#pragma warning(disable: 4512)    // assignment operator could not be generated
#pragma warning(disable: 4610)    // user defined constructor required
#endif

class WordList;

struct Word
{
  const char* const sortedWord;
  const char* const word;

  operator const char*() const { return word; }
};

class WordListIterator : public std::iterator<std::random_access_iterator_tag,
                                              Word>
{
  // The offset of the word in the array of characters.
  std::size_t index;
  const WordList* words;
public:
  WordListIterator(const WordList* list, std::size_t offset);
  WordListIterator(const WordListIterator& that);
  WordListIterator& operator=(const WordListIterator& that);
  bool operator==(const WordListIterator& that) const;
  bool operator!=(const WordListIterator& that) const {return !(*this == that);}

  // Allows iterating forward.
  WordListIterator& operator++();
  WordListIterator& operator++(int);
  WordListIterator& operator+=(unsigned int wordCount);

  // Allows iterating backwards.
  WordListIterator& operator--();
  WordListIterator& operator--(int);
  WordListIterator& operator-=(unsigned int wordCount);

  // The following complement the above basics for a forard_iterator by making
  // this a random access iterator.
  difference_type operator-(const WordListIterator& rhs) const;

  // Returns a pointer to the word in the word list.
  //
  // This is the un-sorted version, i.e the actual/original word.
  char* word() const;

  Word operator*() const;
};

#endif
