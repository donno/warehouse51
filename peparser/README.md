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

For JavaScript/Browser (pe.html)

`$ npm install browserify`
`$ browserify pe-html -o pe-html-bundle.js`

Open pe.html in a web browser, select an executable file and it will output some
data.

Working
---------------------
It it possible to parse the first few parts of the file and parts of the .rsrc
section to read bitmap resources.

TODO
---------------------
The things I would like to see done first are:

* Create a HTML page that uses the JavaScript implementation which allows the
  user to provide a executable file and it lists the information (values) in
  a browser. This is what pe.html does but I would like to theme it better and
  provide support for handling enumerations, flags and also the ability to
  switch between decimal and hexadecimal display. It also needs some styling.

Authors
---------
 * Sean Donnellan <darkdonno@gmail.com>

License
---------------------
The MIT License (see LICENSE.txt)
