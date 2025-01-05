#include <SDL3/SDL.H>

constexpr int padding = 80;

void DrawBoard(SDL_Renderer *renderer) {
  // Another option would be to pre-render the board to a surface and
  // only re-renderer it if the resize event occurs.

  int screen_width, screen_height;
  SDL_GetCurrentRenderOutputSize(renderer, &screen_width, &screen_height);

  // The board should be a square such that the sides should all have the same
  // length and angles should all be 90 degrees.
  const auto board_size = screen_width < screen_height
                              ? screen_width - padding * 2.0f
                              : screen_height - padding * 2.0f;
  const auto cell_size = board_size / 8.0f;

  // The board should be centred in the window.
  SDL_FRect board_rectangle = {(screen_width - board_size) / 2.0f,
                               (screen_height - board_size) / 2.0f, board_size,
                               board_size};

  // Draw the dark colour squares.
  SDL_SetRenderDrawColor(renderer, 209, 139, 71, SDL_ALPHA_OPAQUE);
  SDL_RenderFillRect(renderer, &board_rectangle);

  // Draw the light colour squares.
  SDL_FRect cells[8 * 4];
  for (auto y = 0; y < 8; ++y)
    for (auto x = 0; x < 4; ++x) {
      auto &cell = cells[x + y * 4];
      cell.x = board_rectangle.x + (2 * x + (y & 1)) * cell_size;
      cell.y = board_rectangle.y + y * cell_size;
      cell.w = cell_size;
      cell.h = cell_size;
    }
  SDL_SetRenderDrawColor(renderer, 255, 206, 158, SDL_ALPHA_OPAQUE);
  SDL_RenderFillRects(renderer, cells, SDL_arraysize(cells));

  // Draw border around the board.
  SDL_SetRenderDrawColor(renderer, 0, 0, 0, SDL_ALPHA_OPAQUE);
  SDL_RenderRect(renderer, &board_rectangle);
}

int main() {
  SDL_Init(SDL_INIT_VIDEO);

  SDL_Window *window;
  SDL_Renderer *renderer;
  if (!SDL_CreateWindowAndRenderer("Chess Viewer", 1024, 768,
                                   SDL_WINDOW_RESIZABLE, &window, &renderer)) {
    SDL_LogError(SDL_LOG_CATEGORY_APPLICATION,
                 "Couldn't create window and renderer: %s", SDL_GetError());
    return 3;
  }

  SDL_Surface *surface;
  for (SDL_Event event; true; ) {
    SDL_PollEvent(&event);
    if (event.type == SDL_EVENT_QUIT) {
      break;
    }

    SDL_SetRenderDrawColor(renderer, 38, 36, 33, 0x00);
    SDL_RenderClear(renderer);
    DrawBoard(renderer);
    SDL_RenderPresent(renderer);
  }

  SDL_DestroyRenderer(renderer);
  SDL_DestroyWindow(window);
  SDL_Quit();
}
