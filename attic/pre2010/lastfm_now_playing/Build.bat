echo off
call "C:\Program Files\RosBE\MinGW.cmd"
gcc -Wall -Os -DWIN32 -c findwindow.c -o plugin.o
dllwrap --def plugin.def --dllname pluginlastfmnp.dll plugin.o
del plugin.o
echo Plugin Built
echo /load D:\Sean\Coding\C\LFMNP\pluginlastfmnp.dll
echo /load D:\Sean\Coding\C\LFMNP\pluginlastfmnp.dll | clip
