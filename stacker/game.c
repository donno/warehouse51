#include "state.h"

#include <math.h>

#define TOWER_WIDTH 7
#define TOWER_HEIGHT 10

#define PLAYER_WIDTH 3
#define PLAYER_DEF_MOVECOUNT 15

#define GAMEOVER_STILLPLAYING 0
#define GAMEOVER_WIN 1
#define GAMEOVER_LOSE (-1)

SDL_Surface *blockRed;
SDL_Surface *blockOrange;
SDL_Surface *blockGreen;

SDL_Surface *block;
SDL_Rect blockbase;

struct Player {
    SDL_Surface *block;
    SDL_Rect    rect;
    short       positionX;
    short       currentY;
    short       velocity;
    short       moveCount;
    short       gameover;
} player;

bool blockActive[TOWER_WIDTH][TOWER_HEIGHT];

void InitGame(void) {
    int x;
    int y;
    blockOrange  = SDL_CreateRGBSurface(SDL_SWSURFACE, 52, 48, 16, 0, 0,0 ,0);
    blockGreen = SDL_CreateRGBSurface(SDL_SWSURFACE, 52, 48, 16, 0, 0,0 ,0);
    blockRed   = SDL_CreateRGBSurface(SDL_SWSURFACE, 52, 48, 16, 0, 0,0 ,0);
    player.block = SDL_CreateRGBSurface(SDL_SWSURFACE, 52*PLAYER_WIDTH, 48, 16, 0, 0,0 ,0);
    block = blockOrange;

    SDL_FillRect(blockOrange , &block->clip_rect, SDL_MapRGB(block->format, 220,100,32));
    SDL_FillRect(blockGreen  , &block->clip_rect, 0xFF7E00);
    SDL_FillRect(blockRed    , &block->clip_rect, SDL_MapRGB(block->format, 184,32,32));
    SDL_FillRect(player.block, &player.block->clip_rect, 0x007EFF);

    for (x = 0; x < TOWER_WIDTH; x++) {
        for (y = 0; y < TOWER_HEIGHT; y++) {
            blockActive[x][y] = false;
        }
    }

    player.rect.y = 25;
    player.velocity = 1;
    player.moveCount = PLAYER_DEF_MOVECOUNT;
    player.currentY = 0;
    player.gameover = GAMEOVER_STILLPLAYING;
}

void CloseGame(void) {
    SDL_FreeSurface(blockOrange);
    SDL_FreeSurface(blockGreen);
    SDL_FreeSurface(blockRed);
    SDL_FreeSurface(player.block);
}


short ActivateBlockHelper(int x, int y) {
    short segmentsLanded = 0;
    if (y == 0) {
        blockActive[x][y] = true;
        blockActive[x+1][y] = true;
        blockActive[x+2][y] = true;
        return 3;
    }
    if (blockActive[x][y-1]) {
        blockActive[x][y] = true;
        segmentsLanded++;
    }
    if (blockActive[x+1][y-1]) {
        blockActive[x+1][y] = true;
        segmentsLanded++;
    }
    if (blockActive[x+2][y-1]) {
        blockActive[x+2][y] = true;
        segmentsLanded++;
    }
    return segmentsLanded;
}

void EventGame(SDL_Event *sdlEvent) {
    if ( sdlEvent->key.type == SDL_KEYUP ) {
        short ret;
        switch (sdlEvent->key.keysym.sym) {
            case SDLK_r:
                CloseGame();
                InitGame();
                break;
            case SDLK_RETURN:
                if (player.gameover != 0) {
                    return;
                }
                // The player pressed the button
                ret = ActivateBlockHelper(player.positionX, player.currentY);
                if (ret == 0) {
                    player.gameover = GAMEOVER_LOSE;
                    return;
                }
                if (player.currentY == TOWER_HEIGHT) {
                    player.gameover = GAMEOVER_WIN;
                }
                player.currentY++;
                break;
        }
    }
}

void DrawGame(SDL_Surface *screen) {
    int x, y;
    SDL_FillRect(screen, &screen->clip_rect, 0x0);
    if (player.gameover == GAMEOVER_WIN) {
        SDL_FillRect(screen, &screen->clip_rect, SDL_MapRGB(screen->format, 32,184,32));
        return;
    } else if (player.gameover == GAMEOVER_LOSE) {
        SDL_FillRect(screen, &screen->clip_rect, SDL_MapRGB(screen->format, 184,32,32));
        return;
    }

    blockbase.x = (screen->w >> 1) - ((block->w * TOWER_WIDTH) >> 1);
    for (x = 0; x < TOWER_WIDTH; x++) {
        blockbase.y = screen->h - block->h;
        for (y = 0; y < TOWER_HEIGHT; y++) {
            block = (y < 4) ? blockGreen : (y > TOWER_HEIGHT - 3) ? blockRed : blockOrange;
            if (blockActive[x][y]) {
                SDL_BlitSurface(block, &block->clip_rect, screen, &blockbase);
            }
            blockbase.y -= block->h;
        }
        blockbase.x += block->w;
    }

    player.rect.x  = (screen->w >> 1) - ((block->w * TOWER_WIDTH) >> 1) + player.positionX * block->w;
    SDL_BlitSurface(player.block, &player.block->clip_rect, screen, &player.rect);

    // Handle Self movement
    player.moveCount--;
    if (player.moveCount == 0) {
        player.positionX += player.velocity;
        if (player.positionX < 0) {
            player.velocity = 1;
            player.positionX = 0;
        } else if (player.positionX > (TOWER_WIDTH - PLAYER_WIDTH)) {
            player.velocity = -1;
            player.positionX = TOWER_WIDTH - PLAYER_WIDTH;
        }
        player.moveCount = PLAYER_DEF_MOVECOUNT;
    }

    SDL_Flip(screen);
}

void SetupStateGame(struct State *state) {
    state->funcInit   = &InitGame;
    state->funcDraw   = &DrawGame;
    state->funcEvent  = &EventGame;
    state->funcDeinit = &CloseGame;
}
