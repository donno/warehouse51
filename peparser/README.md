peparser
=============
Provided the ability to read the PE/COFF format (i.e Portable Executable/Common
Object File Format), more commonly known as the format used for executables
on Microsoft Windows (.exe files).

Implementations
---------------------
* Python - Uses the Construct library for defining the structures and performing
  the most of the parsing. This was mostly a prototype for getting myself
  familiar with how the structures are defined.
* JavaScript - Uses binary-parser library for defining the structures and
  performing most the parsing.

Using
---------------------

For Python (Install Construct)
`$ pip install Construct`
`$ python peparser.py name.exe`

For JavaScript/Node (Install binary-parser):

`$ npm install binary-parser`
`$ node pe.js`

Working
---------------------
It it possible to parse the first few parts of the file and parts of the .rsrc
section to read bitmap resources.

TODO
---------------------
The things I would like to see done first are:

* Create a HTML page that uses the JavaScript implementation which allows the
  user to provide a executable file and it lists the information (values) in
  a browser.
  I already have a working prototype for being able to this it just lacking the
  ability to display the results on the page.

Authors
---------
 * Sean Donnellan <darkdonno@gmail.com>

License
---------------------
The MIT License (see LICENSE.txt)
