# A Makefile for GNU Make that builds stackers.
#
# This requires SDL.

CXX:=clang++
EXEEXT:=
ifeq ($(CXX),clang++)
  CXXFLAGS:=--std=c++11 -Weverything -Wno-c++98-compat -O3 -g
  CC=clang
  LDFLAGS=-lstdc++
else ifeq ($(CXX),cl)
  CXXFLAGS:=/nologo /c /EHsc
  LDFLAGS:=/nologo
  LD:=link
  EXEEXT:=.exe
else
  CXXFLAGS:=--std=c++11 -Wall -Wextra -O3 -g
  CC=g++
  LDFLAGS=-lstdc++
endif
ifeq ($(CC),cl)
  CFLAGS:=/nologo /c /EHsc
  LDFLAGS:=/nologo sdl.lib
  LD:=link
  EXEEXT:=.exe
endif

ifeq ($(CXX),cl)
# Target rules for Microsoft C++ compiler.
%.o: %.cpp
	$(CXX) $(CXXFLAGS) /Fo$@ $<
%$(EXEEXT): %.o
	$(LD) $(LDFLAGS) $^ /OUT:$@
endif

ifeq ($(CC),cl)
# Target rules for Microsoft C compiler.
%.o: %.c
	$(CC) $(CFLAGS) /Fo$@ $<
%$(EXEEXT): %.o
	$(LD) $(LDFLAGS) $^ /OUT:$@
endif


all: stacker$(EXEEXT)

stacker$(EXEEXT): main.o game.o
	# TODO: Figure out why this isn't using hte %.exe: %.o rule above.
	$(LD) $(LDFLAGS) $^ /OUT:$@