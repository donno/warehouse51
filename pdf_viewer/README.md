pdf_viewer
==========
This is an experiment of using PDFium library with
[Simple DirectMedia Layer](1) (SDL) 2.

At the time of writing this README, it is very bare-bones and is really just 
the milestone of opening the PDF, rendering it to an image and then showing it
on screen.

Building
--------
A very basic build scripts is provided at this time for Microsoft Visual Studio
on Windows, as when initially developing this I simply called the Microsoft
Visual C++ compiler directly. I created the script to fetch the third party
libraries simply so I could return to this project later.

I used prebuilt binaries of PDFium from the [pdfium-binaries](2) project by
[bblanchon](3).

### Windows
To build on Windows with Visual Studio

* Run the "x64 Native Tools Command prompt" from Visual Studio
* Run `build.cmd`
* Copy a PDF to the current working directory named `test_doc.pdf` and run
  `pdf_view_sdl2.exe`.

Planned features
----------------
* Fit page to window - first pass at this has been implemented.
* Fit to width with scroll.
* Stretch goal is to have a list of PDFs in a directory shown down the left so
  you can switch between it.
* Stretch goal is to to have text selection and the ability to copy the text.
  * `FPDFText_GetBoundedText()` - Extract unicode text within a rectangular
    boundary on the page.
  * `FPDFText_CountRects()` and `FPDFText_GetRect()` can be used to detect the
  position of text so it can be highlighted.
  * See https://stackoverflow.com/a/50616122

TODO
----
* Add better error handling for if the PDF could not be found.

Notes
-----
- This experiment is intended to be part of a bigger project that I have in
  mind.
- PDFium has an experimental API where it render the content of a page to a
  Skia SkCanvas instead of to a bitmap.
- PDFium has `FPDF_RenderPage()` for Windows which takes a device context (DC).

[0]: https://pdfium.googlesource.com/pdfium/
[1]: https://www.libsdl.org
[2]: https://github.com/bblanchon/pdfium-binaries
[3]: https://github.com/bblanchon
