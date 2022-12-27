
CC=gcc

BINEXT=.exe
LDOBJS=lib/libudis86.a
BIN=bin/x86graph$(BINEXT)

OBJS=bin/x86graph.o

all: $(BIN)

$(BIN): $(OBJS)
	$(CC) -o $(BIN) $(OBJS) $(LDOBJS)

bin/%.o: src/%.c
	$(CC) $(CFLAGS) -c -o $@ $<

run: $(BIN)
	$(BIN) bin/helloworld$(BINEXT)
	
bin/helloworld$(BINEXT): src/helloworld.c
	$(CC) $(CFLAGS) -o $@ $<
