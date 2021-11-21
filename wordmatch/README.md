wordmatch
=============
A C++ program meant for providing answers for the Word game in the British TV
program "Countdown".

How it works
---------------------

There are two parts
* Generating optimised representation of the word list.
* Finding the solutions using the word list.

The optimised part, groups each word of a certain length into a separate file.
The first 8-bytes of the file stores the length of the words in the file.
Then the words are stored as <sortedWord><word>\0\n so for example the word
"carrot" is stored as "acorrtcarrot\0\n". Each word appears in sorted order in
the file to allow for binary searching of a given sequence of letters.

To find the solution, it opens the word list, sorts the letters and makes them
lower case so given TEQSENUIE becomes eeeinqstu. It then searches for that in
the word list, and then prints out the <word> porition of each match.

It then tries each r-length combination of the characters to find if there are
smaller words that match the characters. For example from eeeinqstu it would try
einqstu which is "inquest".

Building
---------------------

On Windows:
`$ nmake -f Makefile.msvc`

On Linux:

`$ make`

How to use
---------------------

First download a word-list to use, and put it in data/wordlist.txt.
The getdata.py Python script can be used fetch a suitable word list from the
Debian package mirror.

`$ python getdata.py`

Next generate the optimised representation of the word list:

`$ wordmatch --generate`

Now find the solution for a sequence of letters

`$ wordmatch TEQSENUIE`

Authors
---------
 * Sean Donnellan <darkdonno@gmail.com>

License
---------------------
The MIT License (see LICENSE.txt or here for convenience)

Copyright (c) 2014 Sean Donnellan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
