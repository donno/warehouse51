/**
    Stackers
    Language: C
    Libaries: SDL

    Author: Sean <darkdonno@gmail.com>
    Version: 0.2
*/

#include "SDL.h"
#include <stdio.h>
#include "state.h"

#define GAME_NAME "Stackers"

DefSetupState(Game)

// Constants
static const int STATE_MENU   = 0;
static const int STATE_ABOUT  = 1;
static const int STATE_GAME   = 2;
static const int STATE_PAUSE  = 3;
static const int STATE_OVER   = 4;
#define STATE_SIZE				5

// Varibles
struct State states[1];
unsigned int State;

/**
    Game Loop - Main working loop

    Features the splash loop, followed by the core game loop
    \param window pointer to the SDL_WIndow providing the window
    \param renderer pointer to the SDL_Render providing the renderer
    \param texture pointer to the SDL_Texture providing a texture.
    \param screen pointer to the SDL_Surface representing the screen
*/
void GameLoop(SDL_Window* window, SDL_Renderer *renderer, SDL_Texture *texture,
              SDL_Surface *screen)
{
    int bQuit = 0;
    SDL_Event event;
    Uint8 appState;
#ifdef HAS_SPLASH_SCREEN
    int splashCount = 100;
#endif

    // Splash Loop
#ifdef HAS_SPLASH_SCREEN
    // Assumes you have blitted your splash screen already
    while( bQuit == 0 && splashCount > 0 ) {
        while( SDL_PollEvent( &event ) ) {
            if (event.type == SDL_QUIT) {
                bQuit = 1;
            }
        }
        splashCount--;
        SDL_Delay(10);
    }
#endif

    State = STATE_MENU;

    states[State].funcInit();
    states[State].funcDraw(screen);

    SDL_UpdateTexture(texture, NULL, screen->pixels, screen->pitch);
    SDL_RenderClear(renderer);
    SDL_RenderCopy(renderer, texture, NULL, NULL);
    SDL_RenderPresent(renderer);

    // Main Game loop
    while( bQuit == 0 ) {
        while( SDL_PollEvent( &event ) ) {
            if (event.type == SDL_QUIT) {
                bQuit = 1;
            } else {
                if ( event.key.type == SDL_KEYUP ) {
                    if (event.key.keysym.sym == SDLK_F4  && event.key.keysym.mod & KMOD_ALT) {
                        bQuit = 1;
                        break;
                    }
                }
                states[State].funcEvent(&event);
            }
        }
        states[State].funcDraw(screen);

        SDL_UpdateTexture(texture, NULL, screen->pixels, screen->pitch);
        SDL_RenderClear(renderer);
        SDL_RenderCopy(renderer, texture, NULL, NULL);
        SDL_RenderPresent(renderer);

        // If the application is minimised put the game to sleep. This way
        // it won't use as many CPU cycles.
        if (SDL_GetWindowFlags(window) & SDL_WINDOW_MINIMIZED)
        {
          SDL_Delay(1000);
        }
    }
}
#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
int WINAPI WinMain( HINSTANCE hInstance, HINSTANCE hPrevInstance,
        LPSTR lpCmdLine, int nCmdShow )
#else
int main(int argc, char *argv[])
#endif
{
    SDL_Window *window;
    SDL_Surface *screen;
    SDL_Renderer *renderer;
    SDL_Texture *texture;

    // Initialize the SDL library
    if ( SDL_Init(SDL_INIT_VIDEO) < 0 ) {
        fprintf(stderr,"Couldn't initialize SDL: %s\n",SDL_GetError() );
        return -1;
    }

    window = SDL_CreateWindow(GAME_NAME,
                              SDL_WINDOWPOS_UNDEFINED,
                              SDL_WINDOWPOS_UNDEFINED,
                              720, 576,
                              0);

    if ( window == NULL ) {
        fprintf(stderr, "Unable to create window: %s\n",SDL_GetError());
        return -2;
    }

    renderer = SDL_CreateRenderer(window, -1, 0);
    if ( renderer == NULL ) {
        fprintf(stderr, "Unable to create renderer: %s\n",SDL_GetError());
        return -4;
    }

    screen = SDL_CreateRGBSurface(0, 720, 576, 32, 0, 0, 0, 0);
    if ( screen == NULL ) {
        fprintf(stderr, "Unable to create surface: %s\n",SDL_GetError());
        return -5;
    }

    texture = SDL_CreateTextureFromSurface(renderer, screen);
    if ( texture == NULL ) {
        fprintf(stderr, "Unable to create texture: %s\n",SDL_GetError());
        return -6;
    }

    SetupStateGame( &states[0]);

    GameLoop(window, renderer, texture, screen);

    SDL_Quit();
    return 0;
}
