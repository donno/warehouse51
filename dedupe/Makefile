CXXFLAGS=-O3 -Wall -Wextra --std=c++1y
LDLIBS=-lboost_graph
LINK.o = $(LINK.cc)
DEDUPE=dedupe
APPLY=apply
DOT=dot

all: test graphs apply

test: output/test_example_remove.list output/test_basic_remove.list

graphs: output/test_example_before.png output/test_basic_before.png \
	output/test_example_after.png output/test_basic_after.png

output:
	mkdir -p output

output/%_remove.list: input/%.dot output $(DEDUPE)
	./$(DEDUPE) $< > $@
	cat $@
	sort $@ -o $@

# This generates the graphs for the original not after the removal.
output/%_before.png: input/%.dot output
	$(DOT) -Tpng $< -o $@

# This generates the graphs after the removal has been applied.
output/%_after.png: output/%_after.dot output
	$(DOT) -Tpng $< -o $@

output/%_after.dot: output/%_remove.list input/%.dot apply
	./$(APPLY) $(filter-out apply,$^) > $@

dedupe: dedupe.o
apply: apply.o
dedupe.o: dedupe.cpp
apply.o: apply.cpp
