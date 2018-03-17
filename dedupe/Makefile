CXXFLAGS=-O3 -Wall -Wextra --std=c++1y
LDLIBS=-lboost_graph
LINK.o = $(LINK.cc)
DEDUPE=dedupe
DOT=dot

all: test graphs

test: output/test_example_remove.list output/test_basic_remove.list

graphs: output/test_example_before.png output/test_basic_before.png

output:
	mkdir -p output

output/%_remove.list: input/%.dot output $(DEDUPE)
	./$(DEDUPE) $< > $@
	cat $@
	sort $@ -o $@

# This generates the graphs for the original not after the removal.
output/%_before.png: input/%.dot output
	$(DOT) -Tpng $< -o $@

dedupe: dedupe.o
dedupe.o: dedupe.cpp
