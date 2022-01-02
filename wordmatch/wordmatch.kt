/*
    NAME         : WordMatch
    SUMMARY      : Match a bunch of jumbled letters with words.
    COPYRIGHT    : (c) 2021 Sean Donnellan. All Rights Reserved.
    LICENSE      : The MIT License (see LICENSE.txt for details)
    DESCRIPTION  : This is was intended to be a solver for the Letters game in
                   Countdown.

    http://en.wikipedia.org/wiki/Countdown_%28game_show%29)

    NOTES        : The following provides some notes on how to build.

    To compile run the following from the parent folder due to it being in
    a package and the package needs to match the folder name.
    kotlinc -include-runtime wordmatch/wordmatch.kt -d wordmatch\wordmatch.jar

    Currently the wordlist can be embeded into the jar under wordmatch/data,
    at this time it is added after the fact to the jar manually.Files

    To prepare the data use getdata.py then use the C++ implementation's
    --generate option to convert from the plain text word list into the native
    data structures.
 */

package wordmatch

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.util.*

const val SIZE_OF_LENGTH = 8

/**
 * A word list contains words all of the same length, as both the word itself
 * and a key which is the sorted letters. The words are always in lower-case as
 * the game does not allow for proper nouns. Typically the input is presented
 * as captial (upper-case) letters.
 *
 * The file is formatted with thge first 8-bytes of the file stores the length
 * of the words in the file. Then the words are stored as
 * <sortedWord><word>\0\n so for example the word"carrot" is stored as
 * "acorrtcarrot\0\n". Each word appears in sorted order in the file to allow
 * for binary searching of a given sequence of letters.
  */
class WordList {
    /** The storage for the words */
    private val words: ByteArray

    /**
     * The length of each word.
     * A word list always contains the same length words.
     */
    private val length: Long

    constructor(source: Path) {
        val resource = this::class.java.getResource(
            source.toString().replace("\\", "/"))

        val content = if (resource != null)
        {
            resource.openStream().readBytes()
        }
        else
        {
            Files.readAllBytes(source)
        }

        // Read the first 8-bytes which is the length.
        // TODO: Determine why the following doesn't work at some point:
        // https://kotlinlang.org/api/latest/jvm/stdlib/kotlin.native/get-long-at.html
        // The answer seems to be despite the JVM part its not supported there,
        // it only works on 'Kotlin Native'.
        length = content[0].toLong() + (content[1].toLong() shl 8) +
            (content[2].toLong() shl 16) + (content[3].toLong() shl 24)

        // It turned out to hard to simply drop the first SIZE_OF_LENGTH number
        // of bytes without also changing the type.
        words = content

        // Hook this up to logging system (debug level).
        // println(
        //     "Reading " + source + " " + content.size + " bytes. " +
        //         "Words are " + length + " long. There are " + wordCount() +
        //         " words."
        // )
    }

    fun wordCount(): Int {
        return (words.size - SIZE_OF_LENGTH) / (length.toInt() * 2 + 2)
    }

    fun matches(letters: String): ArrayList<String> {
        val matchedWords = ArrayList<String>()

        if (letters.length.toLong() != length)
        {
            // Word list doesn't contain any words that long, so skip it.
            return matchedWords;
        }

        // Sort the letters in the word to enable binary search on the word
        // list which already has each word sorted.
        val sortedLetters = letters.lowercase().toCharArray()
        sortedLetters.sort()

        // Perform a binary search for the lower and upper bounds of
        // sortedLetters in "words" skipping the first 8 bytes (which is the
        // length).
        val startEntryIndex = leftMost(String(sortedLetters))
        val endEntryIndex = rightMost(String(sortedLetters))

        for (entryIndex in startEntryIndex until endEntryIndex)
        {
            matchedWords.add(word(entryIndex))
        }

        return matchedWords
    }

    fun word(index: Int): String {
        val start = entryOffset(index) + length.toInt()
        val range = IntRange(start, start + length.toInt() - 1)
        return words.sliceArray(range).toString(Charsets.UTF_8)
    }

    /**
     * The key is simply the letters in the word sorted.
     */
    fun key(index: Int): String {
        val start = entryOffset(index)
        val range = IntRange(start, start + length.toInt() - 1)
        return words.sliceArray(range).toString(Charsets.UTF_8)
    }

    /**
     * Given the index of an entry (i.e the entry number) return the offset to
     * the entry in the byte array (contents).
     */
    private fun entryOffset(index: Int): Int {
        // An entry is the key followed by word, a null terminator for the word
        // and a new line.
        //
        // The null-terminator makes it easier for C & C++ to print out the
        // word and the new line makes it easier to view the resulting file
        // in a text editor.
        val entryLength = length.toInt() * 2 + 2
        return SIZE_OF_LENGTH + index * entryLength
    }

    /**
     * Return the index of the entry whose key is not less than the given
     * value.
     */
    private fun leftMost(sortedLetters: String): Int {
        // As per https://en.wikipedia.org/wiki/Binary_search_algorithm
        var left = 0
        var right = wordCount()
        while (left < right) {
            val midpoint = kotlin.math.floor((left + right) / 2.0).toInt()
            if (key(midpoint) < sortedLetters) {
                left = midpoint + 1
            } else {
                right = midpoint
            }
        }
        return left
    }

    /**
     * Return the index of the entry whose key is greater than the given
     * value or wordCount() if no such element is found.
     */
    private fun rightMost(sortedLetters: String): Int {
        // As per https://en.wikipedia.org/wiki/Binary_search_algorithm
        var left = 0
        var right = wordCount()
        while (left < right) {
            val midpoint = kotlin.math.floor((left + right) / 2.0).toInt()

            if (key(midpoint) > sortedLetters) {
                right = midpoint
            } else {
                left = midpoint + 1
            }
        }
        return right
    }
}

/**
 * Generates r-length subsequences of elements from an input string.
 *
 * This follows itertools.combinations()
 *
 * Consider making this Iterable<String> so a for loop can be used to go over
 * each combination.
 */
class Combination
{
    /** Stores current permutation of indices into the string. */
    private var indices : Array<Int>

    /** The original string. */
    private val base : String

    /** The length of the sub-string. */
    private val rLength : Int

    constructor(source: String, length: Int) {
        // length must be equal to or less than source.length.
        indices = Array<Int>(length) { it }
        base = String(source.lowercase().toCharArray().apply(){ sort() })
        rLength = length
    }

    /** Return the current subsequence. */
    fun current() : String
    {
        val result = CharArray(rLength)
        for (resultIndex in 0 until rLength)
        {
            result[resultIndex] = base[indices[resultIndex]]
        }
        return String(result)
    }

    /**
     * Generate the next permuation and return true if there is another
     * subsequence.
     */
    fun next() : Boolean
    {
        // This is very much an impliatation of the combinations function
        // given by https://docs.python.org/3/library/itertools.html except
        // it doesn't try to be a seperate iterable class.
        for (i in rLength - 1 downTo 0)
        {
            if (indices[i] != i + base.length - rLength)
            {
                indices[i] += 1

                for (j in i + 1 until rLength)
                {
                    indices[j] = indices[j - 1] + 1

                }

                return true
            }
        }

        return false
    }
}

fun main(args: Array<String>) {
    val minimumWordSize = 2
    val maximumWordSize = 15

    if (args.size != 1) {
        println("A single set of letters should be provided.")
        // TODO: Determine if there is a way to return with an exit code from
        // here.
    } else {
        val input = args[0]
        println("Trying to find a match for " + input)
        for (i in kotlin.math.min(maximumWordSize, input.length)
                    downTo minimumWordSize) {
            val wordList = WordList(Paths.get("data/wordlist" + i + ".bin"))
            var combinations = Combination(input, i)
            do
            {
                val matches = wordList.matches(combinations.current())
                if (matches.size > 0) {
                    for (match in matches)
                    {
                        println(match)
                    }
                }
            } while (combinations.next())
        }
    }
}
