#ifndef PDF_VIEWER_PDFIUM_HPP
#define PDF_VIEWER_PDFIUM_HPP
//===----------------------------------------------------------------------===//
//
// NAME         : PDFium
// NAMESPACE    : PDFViewer
// PURPOSE      : Provides a minimal C++ abstraction over the PDFium library.
// COPYRIGHT    : (c) 2024 Sean Donnellan.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Uses scoped-bound resource management for managing the
//                set up and tear down of the library as well as opening and
//                closing a PDF including converting error handling to
//                exceptions.
//
//===----------------------------------------------------------------------===//

#include <fpdfview.h>
#include <cpp/fpdf_scopers.h>

#include <memory>
#include <stdexcept>

namespace PDFViewer
{
    struct PDFiumLibrary
    {
        PDFiumLibrary();
        ~PDFiumLibrary();

    private:
        FPDF_LIBRARY_CONFIG config;
    };

    // Opens the PDF document at the given path.
    //
    // If there is a error, throws PDFLoadFailure.
    //
    // TODO: replace with std::filesystem::path.
    ScopedFPDFDocument OpenDocument(const char* path);

    // An exception raised when loading a PDF fails.
    class PDFLoadFailure : public std::runtime_error
    {
    public:
        PDFLoadFailure(const char* message) : std::runtime_error(message) {}
        PDFLoadFailure(const std::string& message)
        : std::runtime_error(message) {}
    };
}
#endif