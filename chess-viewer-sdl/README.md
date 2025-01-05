chess-viewer-sdl
================

The goal of this project is to:
1. Render a position using [FEN](FEN) (Forsyth–Edwards Notation).
2. Play back a game using [PGN](PGN) (Portable Game Notation).
3. Stretch goal - Watch games from lichess.org

## Implementation

* Uses [Simple DirectMedia Layer (SDL)](SDL) for interacting with
  graphics hardware.

## Third Party

- The zlib licence applies to [SDL](SDL) itself.
- The Unlicense licence applies to [Chess Merida Unicode TrueType font](0).
  This is chess_merida_unicode.ttf within repository and distribution.
- The SIL Open Font License 1.1 applies to [IBM Plex Sans font](1).
  This is IBMPlexSans-Regular.ttf  within repository and distribution.

## Done

* Set-up SDL to open a window
* Render the chess board

## TODO
Almost everything

* Set-up build system
* Show board coordinates
  * Inside board
  * Outside board
  * All on squares
* Render the pieces
* Read FEN
* Read PGN

[FEN]: https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation
[PGN]: https://en.wikipedia.org/wiki/Portable_Game_Notation
[SDL]: https://libsdl.org/
[0]: https://github.com/xeyownt/chess_merida_unicode
[1]: https://github.com/IBM/plex
