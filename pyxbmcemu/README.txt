
The following package of scripts aim to provide a 1-1 mapping
of the internal api libraries for XBMC Media Center project.

Inspired by alexpoet emulator which is now very outdated, and
uses Tk which is not at all pretty. This version shall use
PyGame libary to provide a rich and nicer interface.

This project is from 2009 and so uses Python 2.x.

Authors:
Sean Donnellan <darkdonno@gmail.com

Version:
0.1-git

Website:
none yet


Usage:
	These are purely for operating system based python 	installation and not
    for running in embedded environment such as XBMC Media Center itself.

Known Short comings:
	ControlLabel will straight up crop to text instead of croping to the third
    to last full char and adding three dots
	ControlLabel with setWidth will not recalucate the cropping of text.

Progress:
xbmc     -
    0 / 26 - functions
    class InfoTagMusic
    class InfoTagVideo
    class Keyboard
    class Language
    class PlayList
    class PlayListItem
    class Player
    class Settings
xbmcgui  -
    class Control
    class ControlImage - works but colorKey, aspectRatio and colorDiffuse is unused
    class ControlLabel - works but font, disabled color, hasPath and angle.
