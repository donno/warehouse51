gitsplitter
=============
Splits individual commits or groups of commits into separate branches.

How it works
---------------------

It takes a list of commits and breaks them out into separate branches, by
creating new branches and cherry-picking certain commits into each branch.


How to use
---------------------

Create a file with the following format:

newBranchName[:sourceBranch] commit [commit]*

Where :sourceBranch is optional and if absent is the same as :origin/master.
The last bit just means zero or more commits.

For example:
```
BugFix459 bab47bb20ff63562e01740c806452528417db672

```

`$ gitsplitter.py`




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
