
## Components

* PGN - Portable Game Notation - Parse PGN. 
* UCI - Universal Chess Interface - Talk to an engine via the UCI.
* Renderer - Render a board with the pieces.

I expect there are already crates which handle some of the components above,
specially the PGN and hopefully the UCI.

## Prior Art

Crates that provide functionality needed to work with Chess.

* General
    * rschess
      > A Rust chess library with the aim to be as feature-rich as
        possible 
        * Parsing FEN
        * Parsing PGN
        * Generating FEN andPGN
        * Saving image of a position (i.e. FEN to image).
* PGN Reading
    * pgn-reader - https://github.com/niklasf/rust-pgn-reader
    * w-pgn - https://github.com/KorieDrakeChaney/w-pgn
    * chess_pgn_parser - https://github.com/hwiechers/chess_pgn_parser/
    * pgn-rs - https://github.com/BlueZeeKing/pgn-rs
    * pgnparse -  https://github.com/hyperchessbot/pgnparse#pgnparse
* Renderer
    * Vello
    * Forma by Google engineers - Development ended and hte project was
      archived in 2022 with the main author suggesting Vello.

For PGN reading, the pgn-reader create has the most downloads and was updated
6 months ago.

Basically, rschess looks very promising as it seems to contian everything I'm
after, it can make a move from the UCI notation however there is no example
of it connecting to a UCI engine so it may not provide that out-of-box.


## Plan

- Set-up two engines playing one another
- Render the game 
  - On screen
  - To series of images (PNGs).
  - To video file (MP4).
  - To RTMP stream - unlikely as this is a pain to deal with, best to let
  ffmpeg handle it.
  
