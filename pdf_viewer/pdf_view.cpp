// A PDF viewer using PDFium library.
//
// Things that might be useful:
// - PageSize
// - Metadata
//
// TODO:
// - Single page at a time
// - Continuous page, one after another.


#include "pdfium.hpp"

#include <fpdfview.h>
#include <stdio.h>

int main() {
  PDFViewer::PDFiumLibrary library;
  FPDF_STRING test_doc = "test_doc.pdf";
  ScopedFPDFDocument document = PDFViewer::OpenDocument(test_doc);
  const int page_count = FPDF_GetPageCount(document.get());
  if (page_count == 1) printf("Document has 1 page.");
  else printf("Document has %d pages", page_count);

  return 0;
}
