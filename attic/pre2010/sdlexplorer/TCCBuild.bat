@echo off
echo Building sdExplorer
tcc -c bs.c
tcc -c arraylist.c
tcc sdlExplorer.c arraylist.o bs.o -I%BP%\include -L%BP%\lib -I%BP%\include\winapi -lSDL -lSDL_ttf  -lkernel32 -lSDL_image  -o foobar.exe
tcc sdlExplorer.c arraylist.o bs.o -I%BP%\include -L%BP%\lib -I%BP%\include\winapi -lSDL -lSDL_ttf  -lkernel32 -o foobarni.exe -DNOIMAGES
