// A PDF viewer using PDFium library and SDL2.
//
// This is very much a work-in-progress.

#include "pdfium.hpp"

#include <fpdfview.h>

#define SDL_MAIN_HANDLED
#include <SDL.h>

#include <stdio.h>

ScopedFPDFBitmap render(FPDF_DOCUMENT document, int page_index)
{
  constexpr int targetDpi = 300;
  constexpr int pointsPerInch = 72;

  ScopedFPDFPage page(FPDF_LoadPage(document, page_index));
  const int width =
    static_cast<int>(FPDF_GetPageWidth(page.get()) * targetDpi / pointsPerInch);
  const int height =
    static_cast<int>(FPDF_GetPageHeight(page.get()) * targetDpi / pointsPerInch);
  const int alpha = FPDFPage_HasTransparency(page.get()) ? 1 : 0;
  ScopedFPDFBitmap bitmap(FPDFBitmap_Create(width, height, alpha));  // BGRx

  if (bitmap) {
    FPDF_DWORD fill_color = alpha ? 0x00000000 : 0xFFFFFFFF;
    FPDFBitmap_FillRect(bitmap.get(), 0, 0, width, height, fill_color);

    int rotation = 0;
    int flags = FPDF_ANNOT;
    FPDF_RenderPageBitmap(bitmap.get(), page.get(), 0, 0, width, height,
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


  auto bitmap = render(document.get(), 0);

  SDL_Renderer* const renderer = SDL_CreateRenderer(window, -1, 0);

  // FPDFBitmap_GetFormat() will tell us if its BGR, BGRx or BGx;
  auto screen = SDL_CreateRGBSurfaceWithFormatFrom(
      FPDFBitmap_GetBuffer(bitmap.get()),
      FPDFBitmap_GetWidth(bitmap.get()),
      FPDFBitmap_GetHeight(bitmap.get()),
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

  SDL_UpdateTexture(texture, nullptr, screen->pixels, screen->pitch);
  SDL_RenderClear(renderer);
  SDL_RenderCopy(renderer, texture, nullptr, nullptr);
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
