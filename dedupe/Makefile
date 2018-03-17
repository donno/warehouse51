CXXFLAGS=-O3 -Wall -Wextra --std=c++1y
LDLIBS=-lboost_graph
LINK.o = $(LINK.cc)
DEDUPE=dedupe

test: output/test_example_remove.list output/test_basic_remove.list


output:
	mkdir -p output

output/%_remove.list: input/%.dot output $(DEDUPE)
	./$(DEDUPE) $< > $@
	cat $@
	sort $@ -o $@

dedupe: dedupe.o
dedupe.o: dedupe.cpp
