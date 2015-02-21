"use strict";
//===----------------------------------------------------------------------===//
//
// NAME         : pe-html.js
// SUMMARY      : Parses the PE/COFF format and outputs to to HTML/
// COPYRIGHT    : (c) 2015 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
// DESCRIPTION  : Parse the Microsoft Portable Executable and Common Object File
//                Format which is most commonly used as the format of
//                executables on Microsoft Windows and renders the output to
//                HTML so it can be displayed in a web browser.
//
//===----------------------------------------------------------------------===//

var pe = require('./pe.js');

// Given the structure defintion (Parser()) object used to parse the field,
// associate the variable name with the value.
function formatWithNames(structure, fields, dest)
{
  for (var item = structure.next; item; item = item.next)
  {
    dest.innerHTML +=
      '<li class="item">' +
        '<strong class="name">' + item.varName + ':</strong>' +
        '<span class="value">'  +
           fields[item.varName].toLocaleString() +
            ' (0x' + fields[item.varName].toString(16) + ')' +
        '</span>' +
      '</li>';
  }
};

function writeBitmapToImageToScreen()
{
  var bitmapIndex = 0;
  var bitmapsDiv = document.getElementById('pe-bitmaps');
  bitmapsDiv.innerHTML = '';
  function writeFile(bitmapData)
  {
    var base64EncodedAsciiString = bitmapData.toString('base64')
    bitmapsDiv.innerHTML += '<img src="data:image/bmp;base64,' +
      base64EncodedAsciiString + '">';
  }
  return writeFile;
}

function fileProvided(file)
{
  var reader = new FileReader();
  reader.addEventListener("loadend", function(event) {
    // reader.result contains the contents of blob as a typed array
    var data = new Int8Array(event.target.result);
    var peData = pe.parseFile(data);

    var dest = document.getElementById('pe-results');
    formatWithNames(pe.structures.DosHeader, peData.dosHeader, dest);

    var peHeaderStructure = pe.structures.NtHeader.next.options.type;
    formatWithNames(peHeaderStructure, peData.ntHeader.Main, dest);

    var optionalHeaderStructure = pe.structures.NtHeader.next.next.options.type;
    formatWithNames(optionalHeaderStructure, peData.ntHeader.Optional, dest);

    pe.forEachBitmap(peData, writeBitmapToImageToScreen(), true);
    var bitmapsDiv = document.getElementById('pe-bitmaps');
    if (bitmapsDiv.innerHTML.length === 0)
    {
      bitmapsDiv.innerHTML = 'No bitmaps could be found in the executable';
    }
  });

  // Start the read.
  reader.readAsArrayBuffer(file);
}

// Register the call-back for when a file is provided to the input field.
document.getElementById('file-field').addEventListener("change", function(event)
{
  if (event.target.files.length === 0)
  {
    var dest = document.getElementById('pe-results');
    dest.innerHTML = '';
    var bitmapsDiv = document.getElementById('pe-bitmaps');
    bitmapsDiv.innerHTML = 'No executable has been loaded so there is no ' +
                           'bitmaps to show.';
  }
  else if (event.target.files.length === 1)
  {
    fileProvided(event.target.files[0]);
  }
  else
  {
    alert('Support for multiple files at once has not been implemented');
  }
});

// Make Buffer a global as the binary-parser module generates code which expects
// Buffer to be in the global namespace.
window.Buffer = Buffer;
