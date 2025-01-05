#include <SDL3/SDL.H>
#include <SDL3_ttf/SDL_ttf.h>

#include <memory>

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
  TTF_Init();

  SDL_Window *window;
  SDL_Renderer *renderer;
  if (!SDL_CreateWindowAndRenderer("Chess Viewer", 1024, 768,
                                   SDL_WINDOW_RESIZABLE, &window, &renderer)) {
    SDL_LogError(SDL_LOG_CATEGORY_APPLICATION,
                 "Couldn't create window and renderer: %s", SDL_GetError());
    return 3;
  }

  auto ui_font = TTF_OpenFont("IBMPlexSans-Regular.ttf", 16);
  if (!ui_font) {
    SDL_LogError(SDL_LOG_CATEGORY_APPLICATION,
                 "Failed to load font for user interface: %s", SDL_GetError());
    return 3;
  }

  auto pieces_font = TTF_OpenFont("chess_merida_unicode.ttf", 42);
  if (!pieces_font) {
    SDL_LogError(SDL_LOG_CATEGORY_APPLICATION,
                 "Failed to load font for chess pieces: %s", SDL_GetError());
    return 3;
  }

  std::unique_ptr<TTF_TextEngine, decltype(&TTF_DestroyRendererTextEngine)>
      text_engine(TTF_CreateRendererTextEngine(renderer),
                  TTF_DestroyRendererTextEngine);

  if (!text_engine) {
    SDL_LogError(SDL_LOG_CATEGORY_APPLICATION,
                 "Failed to load font for chess pieces: %s", SDL_GetError());
    return 3;
  }

  SDL_Color text_colour = {255, 255, 255, 255};
  // The order is King, Queen, Rook, Bishop, Knight, Pawn.
  // These are the white pieces.
  const auto outline_pieces_text = "\u2654\u2655\u2656\u2657\u2658\u2659";
  const auto filled_pieces_text = "\uE254\uE255\uE256\uE257\uE258\uE259";
  auto pieces =
      TTF_RenderText_Solid(pieces_font, filled_pieces_text, 0, text_colour);
  if (!pieces) {
    SDL_LogError(SDL_LOG_CATEGORY_APPLICATION,
                 "Failed to draw chess pieces: %s", SDL_GetError());
    return 3;
  }

  auto outlined_pieces =
      TTF_RenderText_Solid(pieces_font, filled_pieces_text, 0, text_colour);
  if (!outlined_pieces) {
    SDL_LogError(SDL_LOG_CATEGORY_APPLICATION,
                 "Failed to draw chess pieces: %s", SDL_GetError());
    return 3;
  }
  const SDL_FRect pieces_bounds = {0.0f, 400.0f, pieces->w * 1.0f,
                                   pieces->h * 1.0f};

  // TODO: Render pieces to a surface and combine.
  auto pieces_texture = SDL_CreateTextureFromSurface(renderer, pieces);
  SDL_DestroySurface(pieces);

  std::unique_ptr<TTF_Text, decltype(&TTF_DestroyText)> title(
      TTF_CreateText(text_engine.get(), ui_font, "Chess Viewer 0.1", 0),
      TTF_DestroyText);

  // There is a cross hashing behind the pieces but not within the pieces
  // themselves. const auto outline_cross_hatch_pieces_text =
  // "\uE154\uE155\uE156\uE157\uE158\uE159";
  std::unique_ptr<TTF_Text, decltype(&TTF_DestroyText)> pieces_text(
      TTF_CreateText(text_engine.get(), pieces_font, filled_pieces_text, 0),
      TTF_DestroyText);

  SDL_Surface *surface;
  for (SDL_Event event; true;) {
    SDL_PollEvent(&event);
    if (event.type == SDL_EVENT_QUIT) {
      break;
    }

    SDL_SetRenderDrawColor(renderer, 38, 36, 33, 0x00);
    SDL_RenderClear(renderer);
    DrawBoard(renderer);

    TTF_DrawRendererText(title.get(), 10, 10);
    SDL_SetRenderDrawColor(renderer, 255, 255, 0, 0x00);

    // Black pieces
    TTF_SetTextColor(pieces_text.get(), 0, 0, 0, 255);
    TTF_DrawRendererText(pieces_text.get(), 10, 500);

    // White pieces
    TTF_SetTextColor(pieces_text.get(), 255, 255, 255, 255);
    TTF_DrawRendererText(pieces_text.get(), 10, 600);

    // Render from pieces_texture
    SDL_RenderTexture(renderer, pieces_texture, nullptr, &pieces_bounds);

    SDL_RenderPresent(renderer);
  }

  TTF_CloseFont(ui_font);
  SDL_DestroyRenderer(renderer);
  SDL_DestroyWindow(window);
  TTF_Quit();
  SDL_Quit();
}
