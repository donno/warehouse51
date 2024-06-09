#include "pdfium.hpp"

#include <string>

PDFViewer::PDFiumLibrary::PDFiumLibrary()
{
  config.version = 2;
  config.m_pUserFontPaths = nullptr;
  config.m_pIsolate = nullptr;
  config.m_v8EmbedderSlot = 0;
  FPDF_InitLibraryWithConfig(&config);
}

PDFViewer::PDFiumLibrary::~PDFiumLibrary()
{
    FPDF_DestroyLibrary();
}

ScopedFPDFDocument PDFViewer::OpenDocument(const char* path)
{
    ScopedFPDFDocument document(FPDF_LoadDocument(path, nullptr));
    if (!document) {
        unsigned long err = FPDF_GetLastError();
        switch (err) {
        case FPDF_ERR_SUCCESS:
            throw PDFLoadFailure("Failure unknown.");
        case FPDF_ERR_UNKNOWN:
            throw PDFLoadFailure("Failure unknown.");
        case FPDF_ERR_FILE:
            throw PDFLoadFailure("File not found or could not be opened.");
        case FPDF_ERR_FORMAT:
            throw PDFLoadFailure("File not in PDF format or corrupted.");
        case FPDF_ERR_PASSWORD:
            throw PDFLoadFailure("Password required or incorrect password.");
        case FPDF_ERR_SECURITY:
            throw PDFLoadFailure("The PDF had an unsupported security scheme.");
        case FPDF_ERR_PAGE:
            throw PDFLoadFailure("Page not found or content error.");
        default:
            throw PDFLoadFailure("Unknown error: " + std::to_string(err));
        }
    }
    return document;
}
