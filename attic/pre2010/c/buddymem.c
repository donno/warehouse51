#include <stdio.h>
#include <stdlib.h>

struct buddyBlock {
    void *mem;
    unsigned int size;
} mainBuddy;

/**
    \param size the size of the memory in bytes
*/
void initBuddyMemory(unsigned int size) {
    printf("initBuddyMemory(%u)\n", size);
    mainBuddy.mem = malloc( size );
    mainBuddy.size = size;
}

void printBuddyMemory() {
    printf("[ %d ]\n", mainBuddy.size);
}

int main() {
    int x;
    printf("Buddy Allocation\n");
    initBuddyMemory(1024 * 1024 * 2); // alllocate 2 mb
    printBuddyMemory();
    scanf("%d", &x);
    return 0;
}
