/*

    -fdata-sections -ffunction-sections -Wl,-gc-sections
    -mno-cygwin
    -fomit-frame-pointer -mcpu=i386
    -fomit-frame-pointer -march=i586
    
    
    gcc sdlExplorer.c bs.c arraylist.c -lSDL -lSDL_ttf -lSDL_image

    <code name="BootStrap Loader" version="0.1">
        int main(int argc, char** argv) {
            return dMain(argc,argv);
        };
    </code>

*/
//#define WINDOWS

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#ifdef WINDOWS
#include <windows.h>
#include <strsafe.h>
#endif

#include <SDL/SDL.h>
#include <SDL/SDL_ttf.h>
#ifndef NOIMAGES
#include <SDL/SDL_image.h>
#endif
#include "arraylist.h"
#define COL_WHITE 16777215 /* 16777215 == Uint32, of color 255,255,255

/* STATIC GUI SURFACES */
static SDL_Surface * surfBG;
static SDL_Surface * surfBNF;
static SDL_Surface * surfBF;
static SDL_Surface * surfIF;
static SDL_Surface * surfSBU;
static SDL_Surface * surfSBD;
static SDL_Surface * surfSB;
static SDL_Surface * surfBD;
static TTF_Font    * mainFont;

/* --- START GUI Based Code --- */
typedef enum guiControlType { GUIBUTTON = 0, GUIIMAGE, GUILABEL } guiControlType;
SDL_Color scWhite = {255,255, 255, 0 };

typedef struct guiControl {
    unsigned int id;
    SDL_Rect pos;
    bool isVisible;
    bool hasFocus;
} guiControl;

struct guiButton;

typedef struct guiButton {
    guiControl c;
    SDL_Surface * textureFocus;
    SDL_Surface * textureNoFocus;
    SDL_Surface * textureText;
    struct guiButton * bl;
    struct guiButton * br;
    struct guiButton * bu;
    struct guiButton * bd;
    char * label;
} guiButton;

typedef struct guiImage {
    guiControl c;
    SDL_Surface texture;
} guiImage;

void createGUIButton( guiButton * gB ,unsigned int id, int x, int y, unsigned int width, unsigned int height,
    char * label, TTF_Font * font) {
    /*printf("_createGUIButton()\n");*/
    gB->c.id = id;
    gB->c.pos.x = x;
    gB->c.pos.y = y;
    gB->c.pos.w = width;
    gB->c.pos.h = height;
    gB->c.hasFocus = false;
    gB->c.isVisible = true;
    gB->textureFocus = surfBF;
    gB->textureNoFocus = surfBNF;
    gB->textureText = TTF_RenderText_Blended( font, label, scWhite );
};

void renderGUIButton( guiButton * gB, SDL_Surface * s) {
    /*printf("_renderGUIButton()\n");*/
    if (gB->c.isVisible == false) {
        return;
    }

    SDL_Rect txt_Rect;
    txt_Rect.x = gB->c.pos.x + 15;
    txt_Rect.y = gB->c.pos.y + 8;
    txt_Rect.w = gB->textureText->w;
    txt_Rect.h = gB->textureText->h;
    if (gB->c.hasFocus == true) {
            if (gB->textureFocus == NULL) {
                SDL_Rect sr =  {gB->c.pos.x,gB->c.pos.y,gB->c.pos.w,gB->c.pos.h};
                SDL_FillRect(s, &sr , 14474460);
            } else {
                SDL_BlitSurface(gB->textureFocus , &gB->textureFocus->clip_rect, s, &gB->c.pos);
            }
    } else {
        if (gB->textureNoFocus == NULL) {
                SDL_Rect sr =  {gB->c.pos.x,gB->c.pos.y,gB->c.pos.w,gB->c.pos.h};
                SDL_FillRect(s, &sr , 6908265);
        } else {
            SDL_BlitSurface(gB->textureNoFocus , &gB->textureNoFocus->clip_rect, s, &gB->c.pos);
        }
    }
    SDL_BlitSurface(gB->textureText , &gB->textureText->clip_rect, s, &txt_Rect);
};

bool checkPointInRect(int x, int y, SDL_Rect r) {
    if (x >= r.x && x <= r.x + r.w) {
        if (y >= r.y && y <= r.y + r.h) {
            return true;
        }
    }
    return false;
};

void setnavGUIButton(guiButton * gB, guiButton * gU, guiButton * gD, guiButton * gL, guiButton * gR) {
    gB->bl = gL;
    gB->br = gR;
    gB->bu = gU;
    gB->bd = gD;
};


guiButton * changeFocus(SDL_Surface * screen, guiButton * curButton, guiButton * newBut) {
    if (newBut == NULL) {
        return curButton;
    }
    curButton->c.hasFocus = false;
    newBut->c.hasFocus = true;
    renderGUIButton(curButton, screen);
    renderGUIButton(newBut, screen);
    SDL_Flip(screen);
    return newBut;
}

/* --- END GUI Based Code --- */
typedef struct FileDirEntry {
    TCHAR fname[MAX_PATH]; /* Windows: TCHAR */
    char type;
    unsigned long size; /* Windows: DWORD */
} FileDirEntry;

ArrayList * GetDirectoryListing() {
    ArrayList * dirList = arraylist_new (25);
    #ifdef WINDOWS
    WIN32_FIND_DATA FFD;
    HANDLE hFind = INVALID_HANDLE_VALUE;
    hFind = FindFirstFile("C:/*", &FFD);
    //hFind = FindFirstFile("file://C:/*", &FFD);
    if (hFind == INVALID_HANDLE_VALUE) {
        /*printf ("Invalid file handle. Error is %u.\n", GetLastError());*/
        return NULL;
    }

    do {
        FileDirEntry * fde;
        fde = malloc(sizeof * fde);
        StringCbCopyN (fde->fname, MAX_PATH, FFD.cFileName, MAX_PATH);
        /*strcat(fde->fname,FFD.cFileName);*/
        fde->size = FFD.nFileSizeLow;
        if (FFD.dwFileAttributes == FILE_ATTRIBUTE_DIRECTORY) {
            fde->type = 'd';
        } else {
            fde->type = 'f';
        }
        arraylist_append(dirList, fde);
    } while (FindNextFile(hFind, &FFD) != 0);
    #endif
    return dirList;
};
/* Return > 0 if 'Wrapping has occured */
unsigned int renderDirList(SDL_Surface * screen, ArrayList * dirList, TTF_Font * font, unsigned int start, bool dirDown) {
    #ifdef NOIMAGES
    const bool showThumb = false;
    #else
    const bool showThumb = true;
    #endif

    const unsigned int itemHeight = 32;
    
    
    SDL_Rect sr;
    sr.x = 0;
    sr.y = 90;
    #ifndef NOIMAGES
    sr.w = surfBG->w;
    sr.h = 90-surfBG->h;
    SDL_BlitSurface(surfBG, &sr , screen, &sr);
    #else
    sr.w = 720;
    sr.h = 576;
    SDL_FillRect(screen, &sr, 0);
    #endif
    unsigned int maxItems = (576 - 95) / itemHeight;
    if (dirDown == false) {
        if (start > 0) {            
            if (start > dirList->length) {
                start = dirList->length - maxItems - 1 - (start - dirList->length);
            } else if (start-1 > maxItems) {
                start = start - maxItems*2 - 2;
            } else {
                start = 0;
            }
        }
    }

    int i;
    for (i=start; i< dirList->length; ++i) {
        FileDirEntry * cfde;
        SDL_Surface * fi;

        cfde = (FileDirEntry *) dirList->data[i];
        fi = TTF_RenderText_Blended( font, cfde->fname, scWhite );

        SDL_Rect dest = { 15, 95 +(i-start)*itemHeight,fi->w,fi->h };

        if (showThumb == true && surfIF != NULL) {
            if (cfde->type == 'd') {
                SDL_BlitSurface(surfIF , &surfIF->clip_rect, screen, &dest);
            }
            dest.y = dest.y + 4;
            dest.x = 15+itemHeight+15;
        }
        SDL_BlitSurface(fi , &fi->clip_rect, screen, &dest);
        //printf("%25s    [%c]    %i bytes\n", cfde->fname, cfde->type, cfde->size);
        if (95+(i-start)*itemHeight > 576) {
            return i;
        }
    }
    return dirList->length+(i-start);
};

void ShowDialog(SDL_Surface *screen, TTF_Font * tFont) {
    SDL_Surface * path = TTF_RenderText_Blended( tFont, "sdExplorer: Help", scWhite );
    
    #ifndef NOIMAGES
        SDL_Rect dest = {(720-surfBD->w)/2,(576-surfBD->h)/2,0,0};
        SDL_BlitSurface(surfBD, &surfBD->clip_rect, screen, &dest);
    #else
        SDL_Rect dest =  {137,121,446,334};
        SDL_FillRect(screen, &dest , 6908265);
    #endif
    dest.x += 15;
    dest.y += 5;
    SDL_BlitSurface(path, &path->clip_rect, screen, &dest);

};

void OnControl(unsigned int id, SDL_Surface * screen) {
    if (id == 1) {
        printf("MENU: File\n");
    } else if (id == 2) {
        printf("MENU: Edit\n");
    } else if (id == 3) {
        printf("MENU: View\n");
    } else if (id == 4) {
        printf("MENU: Tools\n");
    } else if (id == 5) {
        printf("MENU: Help\n");
        ShowDialog(screen, mainFont);
        SDL_Flip(screen);
    } else {
        printf("UNKNOWN BUTTON ID: %i\n",id );
    }
};


int dMain(int argc, char** argv) {
/*int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nShowCmd){*/
    ArrayList * dirList = GetDirectoryListing();
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
    SDL_WM_SetCaption( "sdExplorer" , NULL ); /* Set Window Title */

    /* screen = SDL_SetVideoMode(720, 576, 0, SDL_SWSURFACE); */
    /* screen = SDL_SetVideoMode(720, 576, 0, SDL_DOUBLEBUF | SDL_FULLSCREEN); */
    screen = SDL_SetVideoMode(720, 576, 0, SDL_DOUBLEBUF);

    if ( screen == NULL ) {
        fprintf(stderr,"Unable to set video mode: %s\n",SDL_GetError() );
        return 1;
    }

    /* INIT RESOURCES */
    #ifdef NOIMAGES
        surfBG  = NULL;
        surfBNF = NULL;
        surfBF  = NULL;
        surfIF  = NULL;
        surfSB = NULL;
    #else
        surfBG  = IMG_Load("images/background.png");
        surfBNF = IMG_Load("images/button-nofocus.png");
        surfBF  = IMG_Load("images/button-focus.png");
        surfIF  = IMG_Load("images/DefaultFolder32.png");
        surfBD  = IMG_Load("images/dialog-panel2.png");
        surfSBU = IMG_Load("images/scrollbar_arrow_up_focus.png");
        surfSBD = IMG_Load("images/scrollbar_arrow_down_focus.png");
        surfSB = IMG_Load("images/scrollbar_bar.png");    
    #endif

    mainFont = TTF_OpenFont( "vera.ttf" , 14 );
    if (mainFont == NULL) {
        printf("Font Failed to load\n");
        return;
    }
    
    SDL_Surface * path = TTF_RenderText_Blended( mainFont, "Path: C:/", scWhite );
    SDL_Rect srp = { 15,32,path->w,path->h };
    /* Create Buttons */
    guiButton * curButton;
    guiButton butFile;
    guiButton butEdit;
    guiButton butView;
    guiButton butTool;
    guiButton butHelp;
    guiButton guiList;
    guiButton * guiButtons[5];
    guiButtons[0] = &butFile;
    guiButtons[1] = &butEdit;
    guiButtons[2] = &butView;
    guiButtons[3] = &butTool;
    guiButtons[4] = &butHelp;
    
    createGUIButton(&butFile, 1, 0   , 0, 84, 28, "File" , mainFont);
    createGUIButton(&butEdit, 2, 84  , 0, 84, 28, "Edit" , mainFont);
    createGUIButton(&butView, 3, 84*2, 0, 84, 28, "View" , mainFont);
    createGUIButton(&butTool, 4, 84*3, 0, 84, 28, "Tools", mainFont);
    createGUIButton(&butHelp, 5, 84*4, 0, 84, 28, "Help" , mainFont);
    createGUIButton(&guiList, 6, 15, 95, 690, 466,"", mainFont);
    
    setnavGUIButton(&butFile, NULL, &guiList, &butHelp, &butEdit);
    setnavGUIButton(&butEdit, NULL, &guiList, &butFile, &butView);
    setnavGUIButton(&butView, NULL, &guiList, &butEdit, &butTool);
    setnavGUIButton(&butTool, NULL, &guiList, &butView, &butHelp);
    setnavGUIButton(&butHelp, NULL, &guiList, &butTool, &butFile);
    setnavGUIButton(&guiList, &guiList, &guiList, &guiList, &guiList);

    guiList.c.isVisible = false;
    butFile.c.hasFocus = true;
    curButton = &butFile;

    #ifndef NOIMAGES
    SDL_BlitSurface(surfBG, &surfBG->clip_rect, screen, &surfBG->clip_rect);
    /*SDL_Rect d = {720-15-32, 95,0,0};
    SDL_BlitSurface(surfSBU, &surfSBU->clip_rect, screen, &d);
    SDL_Rect d2 = {720-15-32, 100,0,0};
    SDL_BlitSurface(surfSB, &surfSB->clip_rect, screen, &d2);*/
    #else
    /*SDL_FillRect(screen, &screen->clip_rect, 16777215); *//*BG Color (leave so its just black*/
    #endif

    renderGUIButton(&butFile, screen);
    renderGUIButton(&butEdit, screen);
    renderGUIButton(&butView, screen);
    renderGUIButton(&butTool, screen);
    renderGUIButton(&butHelp, screen);
    unsigned int botList = renderDirList(screen, dirList, mainFont, 0, true);
    SDL_BlitSurface(path , &path->clip_rect, screen, &srp);
    SDL_Flip(screen);

    /* Screen Rendered Enter Event loop*/
    SDL_Event event;
    int bQuit = 0;
    while( bQuit == 0 ) {
        while( SDL_PollEvent( &event ) ) {
            if (event.type == SDL_QUIT) {
                bQuit = 1;
            } else if ( event.key.type == SDL_KEYUP ) {
                if (event.key.keysym.sym == SDLK_UP) {
                    curButton = changeFocus(screen, curButton, curButton->bu);
                } else if (event.key.keysym.sym == SDLK_DOWN) {
                    curButton = changeFocus(screen, curButton, curButton->bd);
                } else if (event.key.keysym.sym == SDLK_LEFT) {
                    curButton = changeFocus(screen, curButton, curButton->bl);
                } else if (event.key.keysym.sym == SDLK_TAB) {
                    curButton = changeFocus(screen, curButton, curButton->br);
                } else if (event.key.keysym.sym == SDLK_RIGHT) {
                    curButton = changeFocus(screen, curButton, curButton->br);
                } else if (event.key.keysym.sym == SDLK_RETURN) {
                    OnControl(curButton->c.id,screen);
                } else if (event.key.keysym.sym == SDLK_PAGEDOWN) {
                    if (botList < dirList->length) {
                        botList = renderDirList(screen, dirList, mainFont, botList, true);
                        SDL_Flip(screen);
                    }                    
                } else if (event.key.keysym.sym == SDLK_PAGEUP) {
                    botList = renderDirList(screen, dirList, mainFont, botList, false);
                    SDL_Flip(screen);
                }
            } else if ( event.key.type == SDL_MOUSEMOTION) {
                int i;
                if (event.motion.y < 30) { /* This if is only in place to speed up since all buttons are above there */
                for (i = 0; i < 5; i++) {
                    if (checkPointInRect(event.motion.x,event.motion.y, guiButtons[i]->c.pos)) {
                        curButton = changeFocus(screen, curButton, guiButtons[i]);
                    }
                }
                }
            } else if ( event.key.type == SDL_MOUSEBUTTONUP ) {
                if (event.button.button == SDL_BUTTON_LEFT) {
                    int i;
                    if (event.button.y < 30) { /* This if is only in place to speed up since all buttons are above there */
                        for (i = 0; i < 5; i++) {
                            if (checkPointInRect(event.button.x,event.button.y, guiButtons[i]->c.pos)) {
                                OnControl(guiButtons[i]->c.id,screen);
                            }
                        }
                    }
                }
            }
        }
    }

    /* Free Resources */
    arraylist_free(dirList);
    free(dirList);
    TTF_CloseFont(mainFont);
    SDL_FreeSurface(surfBG);
    SDL_FreeSurface(surfBNF);
    SDL_FreeSurface(surfBF);
    return 0;
}
