numberhunt
=============
A Python script meant for providing solution for the Numbers game in the
British TV program "Countdown". It is also intended to provide an interactive
environment where the game can be played with the intention that it is played
by a machine.

Game rules
---------------------

The rules of the game are:
- A target number is selected. Between 100 and 999 inclusive.
- Six numbers are selected from the pool of [25, 50, 75, 100] and the
  numbers 1 to 10 each appearing twice.
- Using the six numbers attempt to get the target number (or closest) using
  addition, subtraction, multiplication and division.
- All six numbers aren't required.
- Division is only valid if the result is an integer.

Scoring is
- 10 points for the getting the exact solution
- 7 points for 5 away
- 5 points within 10 points
- 0 if neither.

How it works
---------------------

The solver is essentially brute-force and runs through all the combinations
of actions which is using up to six numbers and applying the operations to
them. 

It presents the expression in postifx notation. The final result could be
converted to inflex notation.

The `Game` class represents the the system as a 'game' where by you think of it
as being a single player turn-based game.

The actions are pick one of the six numbers, or one of the for operators (addition, subtraction, multiplication and division). And ideally, you
would keep going until you run out of time, or if it was going to be human
playable like this reset / undo would be an option to.

There is only one possible way you could win by choosing a single number which
is if the target is 100 and you have an 100 to choose from. Otherwise you need
at least two numbers at the start as all operators are binary so need to
arguments (the two numbers). The third choice does not need to be a operator
as you can choose 100, 25, 5  then do * resulting in 125 and then + resulting
in 125.

Authors
---------
 * Sean Donnellan <darkdonno@gmail.com>

License
---------------------
The MIT License (see LICENSE.txt or here for convenience)

Copyright (c) 2021 Sean Donnellan

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
