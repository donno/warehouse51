# A Makefile for GNU Make that builds wordmatch.
CXX:=clang++
ifeq ($(CXX),clang++)
  CXXFLAGS:=--std=c++11 -Weverything -Wno-c++98-compat -O3 -g
else
  CXXFLAGS:=--std=c++11 -Wall -Wextra -O3 -g
endif

wordmatch: wordmatch.cpp

wordmatch.cpp: wordlist.hpp wordlistiterator.hpp

getdata:
	@python getdata.py
