/**
    Stackers
    Language: C
    Libaries: SDL

    Author: Sean <darkdonno@gmail.com>
    Version: 0.2
*/

#include <SDL/SDL.h>
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

    Features the spalsh loop, followed by the core game loop
    \param screen pointer ot the SDL_Surface representing the screen
*/
void GameLoop(SDL_Surface *screen) {
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

    SDL_Flip(screen);

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
        SDL_Flip(screen);

        // This will put the app to sleep if its not active
        // Very good for when u minimize it
        appState = SDL_GetAppState();
        if ((appState == SDL_APPACTIVE) || (!appState) )  {
            SDL_Delay(1000) ;
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
    SDL_Surface *screen;

    // Initialize the SDL library
    if ( SDL_Init(SDL_INIT_VIDEO) < 0 ) {
        fprintf(stderr,"Couldn't initialize SDL: %s\n",SDL_GetError() );
        return -1;
    }

    SDL_WM_SetCaption( GAME_NAME , GAME_NAME );
    screen = SDL_SetVideoMode(720, 576, 0, SDL_DOUBLEBUF);

    if ( screen == NULL ) {
        fprintf(stderr,"Unable to set video mode: %s\n",SDL_GetError() );
        return -3;
    }

    SetupStateGame( &states[0]);

    GameLoop(screen);

    SDL_Quit();
    return 0;
}
