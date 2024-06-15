// A PDF viewer using PDFium library and SDL2.
//
// This is very much a work-in-progress.

#include "pdfium.hpp"

#include <fpdfview.h>

#define SDL_MAIN_HANDLED
#include <SDL.h>

#include <stdio.h>

namespace
{
  namespace internal
  {
    enum class Sizing
    {
      FitToPage,
      FitToWidth,
    };

    // Adjust the sizing of the page to fit the entire page in the viewport.
    //
    // This will often mean if the window/viewport is not the large enough on
    // screen most hte document will be too small.
    //
    // The starting X or Y is adjusted so it is in the centre of the screen.
    void FitToPage(int screen_width, int screen_height,
                  int* width, int* height,
                  int* x, int* y);

    // Adjust the sizing of the page to fit the the width of the page in the
    // given screen width, such that the page will be shown from the left most
    // of the window to the right most.
    void FitToWidth(int screen_width, int screen_height,
                    int* width, int* height);
  }
}

void internal::FitToPage(
  int screen_width, int screen_height,
  int* width, int* height,
  int* x, int* y)
{
  if (*width / screen_height >= *height / screen_height)
  {
    // Size the page based on the width, such that the full page fits in the
    const auto new_height = *height * screen_width / screen_height;
    *x = 0;
    *y = *height - new_height / 2;
    *height = new_height;
  }
  else
  {
    // Fit to height.
    const auto new_width = *width * screen_height / screen_width;
    *x = *width - new_width  - new_width / 2;
    *y = 0;
    *width = new_width;
  }
}

void internal::FitToWidth(
  int screen_width, int screen_height,
  int* width, int* height)
{
  if (screen_width > *width)
  {
    *width = screen_width;
    //*height = //
    puts("Not yet implemented.");
  }
  else
  {
    // This should be the default...
  }
}

ScopedFPDFBitmap render(FPDF_DOCUMENT document, int page_index,
                        int screen_width, int screen_height,
                        internal::Sizing sizing)
{
  constexpr int targetDpi = 600;
  constexpr int pointsPerInch = 72;

  ScopedFPDFPage page(FPDF_LoadPage(document, page_index));
  int width =
    static_cast<int>(FPDF_GetPageWidth(page.get()) * targetDpi / pointsPerInch);
  int height =
    static_cast<int>(FPDF_GetPageHeight(page.get()) * targetDpi / pointsPerInch);

  const int alpha = FPDFPage_HasTransparency(page.get()) ? 1 : 0;
  ScopedFPDFBitmap bitmap(FPDFBitmap_Create(width, height, alpha));  // BGRx

  if (bitmap) {
    FPDF_DWORD fill_color = alpha ? 0x00000000 : 0xFFFFFFFF;
    FPDFBitmap_FillRect(bitmap.get(), 0, 0, width, height, fill_color);

    int x = 0;
    int y = 0;

    switch (sizing)
    {
    case internal::Sizing::FitToPage:
      // Consider if its possible instead having the bitmap only contain the page
      // and so the centring for fit-to-page is performed when the resulting
      // bitmap is written to screen.
      internal::FitToPage(screen_width, screen_height,
                          &width, &height, &x, &y);
      break;
    case internal::Sizing::FitToWidth:
      //internal::FitToWidth(screen_width, screen_height, &width, &height);
      break;
    }

    int rotation = 0;
    int flags = FPDF_ANNOT | FPDF_LCD_TEXT;
    FPDF_RenderPageBitmap(bitmap.get(), page.get(), x, y, width, height,
                          rotation, flags);
  } else {
    fprintf(stderr, "Page was too large to be rendered.\n");
    exit(EXIT_FAILURE);
  }
  return bitmap;
}

int main() {
  PDFViewer::PDFiumLibrary library;

  FPDF_STRING test_doc = "test_doc.pdf";
  ScopedFPDFDocument document;
  try
  {
    document = PDFViewer::OpenDocument(test_doc);
  }
  catch (const PDFViewer::PDFLoadFailure& failure)
  {
    fprintf(stderr, "Failed to open PDF: %s\n", failure.what());
    return 1;
  }

  if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER) != 0)
  {
      printf("Error: %s\n", SDL_GetError());
      return -1;
  }
  auto window = SDL_CreateWindow("PDF Viewer",
                                 SDL_WINDOWPOS_UNDEFINED,
                                 SDL_WINDOWPOS_UNDEFINED,
                                 1920, 1080,
                                 0);

  const auto sizing = internal::Sizing::FitToWidth;
  // TODO: If fitting to width/height then draw the outline of the page to
  // separate the page/document from the background of the application.
  auto bitmap = render(document.get(), 0, 1920, 1080, sizing);

  SDL_Renderer* const renderer = SDL_CreateRenderer(window, -1, 0);

  const auto rendered_page_width = FPDFBitmap_GetWidth(bitmap.get());
  const auto rendered_page_height = FPDFBitmap_GetHeight(bitmap.get());

  // FPDFBitmap_GetFormat() will tell us if its BGR, BGRx or BGx;
  auto screen = SDL_CreateRGBSurfaceWithFormatFrom(
      FPDFBitmap_GetBuffer(bitmap.get()),
      rendered_page_width,
      rendered_page_height,
      32,
      FPDFBitmap_GetStride(bitmap.get()),
      SDL_PIXELFORMAT_BGR888);
  if (!screen) {
      fprintf(stderr, "Unable to create surface: %s\n",SDL_GetError());
      SDL_FreeSurface(screen);
      goto POST_SCREEN_CLEANUP;
  }
  auto texture = SDL_CreateTextureFromSurface(renderer, screen);
  if ( !texture ) {

      goto POST_SCREEN_CLEANUP;
  }

  // If fitting the width of hte page in the width of the viewport, then
  // this should not render teh entire image.
  SDL_UpdateTexture(texture, nullptr, screen->pixels, screen->pitch);
  SDL_RenderClear(renderer);

  switch (sizing)
  {
    case internal::Sizing::FitToPage:
    {
      // The enter image should be shown.
      SDL_RenderCopy(renderer, texture, nullptr, nullptr);
      break;
    }
    case internal::Sizing::FitToWidth:
    {
      // Only part of the image should be shown.
      // TODO: Allow the user to scroll down.
      int window_width;
      int window_height;
      SDL_GetWindowSize(window, &window_width, &window_height);
      const auto screen_aspect_ratio =
        window_height / static_cast<double>(window_width);

      SDL_Rect source = {0, 0, rendered_page_width, static_cast<int>(rendered_page_width * screen_aspect_ratio) };
      SDL_RenderCopy(renderer, texture, &source, nullptr);
      break;
    }
  }

  SDL_RenderPresent(renderer);

  SDL_Event event;
  bool quit = false;
  while (!quit) {
      while( SDL_PollEvent( &event ) ) {
          if (event.type == SDL_QUIT) {
              quit = true;
              continue;
          } else {
              if ( event.key.type == SDL_KEYUP ) {
                  if (event.key.keysym.sym == SDLK_F4 &&
                      event.key.keysym.mod & KMOD_ALT) {
                      quit = true;
                      break;
                  }
              }
          }
      }

      // If the application is minimised put the game to sleep. This way
      // it won't use as many CPU cycles.
      if (SDL_GetWindowFlags(window) & SDL_WINDOW_MINIMIZED)
      {
        SDL_Delay(1000);
      }
  }
  SDL_DestroyTexture(texture);
  SDL_FreeSurface(screen);
POST_SCREEN_CLEANUP:
  SDL_DestroyRenderer(renderer);
  SDL_DestroyWindow(window);
  SDL_Quit();
  return 0;
}
