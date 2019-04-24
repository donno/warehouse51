pymagic
=============
A collection of modules and scripts for working with Magic the Gathering.

The core part of this is to read in list of cards in a format I came up with
and felt was easy for data input. It then aims to convert it into other
formats.

As of April 2019, this was a pre-release and wasn't really intended to be
useful for anyone else so it is likely in an incomplete state.

File format
---------------------
<set code>
===
<card number>
<card number>
<card number>
<card number>
<card number>

# A hash begins a comment.
<set code> # also a comment
===
<card number> # Can also be comment
<card number>
<card number>
<card number>:P # This is a promo
<card number>:F # This is a foil.

Example file
---------------------
GRN
===
005
006

RNA
===
004
005

Authors
---------
 * Sean Donnellan <darkdonno@gmail.com>

License
---------------------
The MIT License (see LICENSE.txt or here for convenience)

Copyright (c) 2018 Sean Donnellan

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
