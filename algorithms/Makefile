# A Makefile for GNU Make that builds wordmatch.
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

ifeq ($(CXX),cl)
# Target rules for Microsoft C++ compiler.
%.o: %.cpp
	$(CXX) $(CXXFLAGS) $< /Fo:$@
%$(EXEEXT): %.o
	$(LD) $(LDFLAGS) $< /OUT:$@
endif


all: collatz$(EXEEXT) fibonacci$(EXEEXT)

collatz$(EXEEXT): collatz.o
fibonacci$(EXEEXT): fibonacci.o
