
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#include <SDL/SDL.h>
#include <SDL/SDL_ttf.h>

static TTF_Font    * mainFont;
static TTF_Font    * headerFont;
SDL_Color scWhite = {255, 255, 255, 0 };
SDL_Color scRed   = {255,   0,   0, 0 };
SDL_Color scGreen = {  0, 255,   0, 0 };
SDL_Color scBlue  = {  0,   0, 255, 0 };

const char windowCaption[]    =  "CMovie Browser" ;
const char appCredits   []    =  "By Sean Donno"  ;

/*int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nShowCmd){*/
int dMain(int argc, char** argv) {
    //printf("trainningMessage: %i", sizeof(trainningMessage)/ sizeof(char));
    SDL_Surface *screen;
    /* Initialize the SDL library */
    if ( SDL_Init(SDL_INIT_VIDEO) < 0 ) {
        fprintf(stderr,"Couldn't initialize SDL: %s\n",SDL_GetError() );
        exit(1);
    }

    /* Initialize the SDL_ttf library extention */
    if(TTF_Init() == -1) {
        fprintf(stderr,"Failed to initialize TTF Extention: %s\n",SDL_GetError() );
        exit(1);
    }

    /* Initialize the screen / window */
    SDL_WM_SetCaption( windowCaption, NULL ); /* Set Window Title */
    screen = SDL_SetVideoMode( 1920, 1024 , 0, SDL_DOUBLEBUF);
    /* screen = SDL_SetVideoMode(720, 576, 0, SDL_SWSURFACE); 
       screen = SDL_SetVideoMode(720, 576, 0, SDL_DOUBLEBUF | SDL_FULLSCREEN); */

    if ( screen == NULL ) {
        fprintf(stderr,"Unable to set video mode: %s\n",SDL_GetError() );
        return 1;
    }

    /* INIT RESOURCES */
    mainFont   = TTF_OpenFont( "DejaVuSans.ttf" , 14 );
    headerFont = TTF_OpenFont( "DejaVuSans.ttf" , 26 );
    if (mainFont == NULL || headerFont == NULL) {
        printf("Font Failed to load\n");
        return;
    }
    /* VERA 26: 78 characthers == width */
    /* DejaVuSans 26: ## characthers == width */
    SDL_Surface * headerSurf = TTF_RenderText_Blended( headerFont, windowCaption , scWhite );
    SDL_Surface * mainText   = TTF_RenderText_Blended( mainFont  , trainningMessage, scWhite );
    SDL_Surface * appText    = TTF_RenderText_Blended( mainFont  , appCredits, scWhite );
    
    //SDL_Surface * mainText   = TTF_RenderText_Blended( mainFont  , "123456789123456789123456789123456789123456789123456789123456789123456789123456", scWhite );

    SDL_Rect srp  = { 15, 16, headerSurf->w, headerSurf->h };
    SDL_Rect srpt = { 15, 16+headerSurf->h+16, mainText->w, mainText->h };
    SDL_Rect appTextrec = { 15, 575-15-appText->h , appText->w, appText->h };
    /*SDL_FillRect(screen, &screen->clip_rect, 16777215); *//*BG Color (leave so its just black*/

    SDL_BlitSurface(headerSurf , &headerSurf->clip_rect, screen, &srp );
    SDL_BlitSurface(mainText   , &mainText  ->clip_rect, screen, &srpt);
    SDL_BlitSurface(appText    , &appText   ->clip_rect, screen, &appTextrec);
    SDL_Flip(screen);

    /* Screen Rendered Enter Event loop*/
    SDL_Event event;
    int bQuit = 0;
    
    int input[79];
    int cur = 0;
    SDL_Rect currentPosition  = { 15, 576/2, 0,0 };
    while( bQuit == 0 ) {
        while( SDL_PollEvent( &event ) ) {
            if (event.type == SDL_QUIT) {
                bQuit = 1;
            } else if ( event.key.type == SDL_KEYUP ) {
                int keycode = event.key.keysym.sym;
                if (keycode > 96 && keycode < 123 || keycode  == 32 || keycode == 46) {
                    /* Check for Shift for uper case VS lower case*/
                    if (event.key.keysym.mod & KMOD_LSHIFT && keycode > 46) {
                        keycode = keycode - 32;
                    }
                    char * c = malloc(sizeof(char));
                    sprintf( c, "%c", keycode );
                    //printf("%c|%c\n", keycode, trainningMessage[cur]);
                    SDL_Color sc = scWhite;
                    if (keycode == trainningMessage[cur]) {
                        sc = scGreen;
                    } else {
                        sc = scRed;
                    }

                    SDL_Surface * text   = TTF_RenderText_Blended( mainFont  , c, sc );
                    currentPosition.w = text->w;
                    currentPosition.h = text->h;
                    SDL_BlitSurface(text , &text->clip_rect, screen, &currentPosition ); 
                    SDL_Flip(screen);
                    currentPosition.x += text->w;
                    
                    
                    cur++;
                    //currentPosition.y += text->h;
                } else if (keycode == 27) {
                    bQuit = 1; /* Escape Pressed*/
                } else if (keycode == 283) { // F2 - For Testing
                    printf("F2 - Clear Text\n");
                    SDL_FillRect(screen, &srpt, 0); //*BG Color (leave so its just black)
                    SDL_Flip(screen);
                } else if (keycode == 284) {
                    printf("F3 - Completed Text\n");
                    //SDL_FillRect(screen, &srpt, 0); //*BG Color (leave so its just black)
                    SDL_Flip(screen);
                } else if (keycode == 285) {
                    printf("F4 - Draw Stats\n");
                    //SDL_FillRect(screen, &srpt, 0); //*BG Color (leave so its just black)
                    SDL_Flip(screen);
                } else {
                    printf("%i", keycode );
                }
                
                /*if (event.key.keysym.sym == SDLK_UP) {
                } else if (event.key.keysym.sym == SDLK_DOWN) {
                } else if (event.key.keysym.sym == SDLK_LEFT) {
                } else if (event.key.keysym.sym == SDLK_TAB) {
                } else if (event.key.keysym.sym == SDLK_RIGHT) {
                } else*/ 
                if (event.key.keysym.sym == SDLK_RETURN) {
                }
            } else if ( event.key.type == SDL_MOUSEMOTION) {
            } else if ( event.key.type == SDL_MOUSEBUTTONUP ) {
                if (event.button.button == SDL_BUTTON_LEFT) {
                }
            }
        }
    }

    /* Free Resources */
    SDL_FreeSurface(headerSurf);
    SDL_FreeSurface(mainText);
    SDL_FreeSurface(appText);
    TTF_CloseFont(mainFont);
    TTF_CloseFont(headerFont);
    return 0;
}
