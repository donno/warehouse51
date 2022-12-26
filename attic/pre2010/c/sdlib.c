/*
    By Donno
*/
#include <stdlib.h>
#include <stdio.h>
#define MALLOC_CALL 1024


unsigned int c = 0;
void * memArray[MALLOC_CALL];
int memArraySize[MALLOC_CALL];

unsigned long int total_allocated;
unsigned long int total_freed;
unsigned long int current_total;

void * _malloc ( unsigned int size ) {
    void* p = malloc( size );
    printf("malloc: %p %d\n", p, size );
    total_allocated += size;
    memArray[c] = p;
    memArraySize[c] = size;
    c++;
    return p;
    
}

void _free ( void * p ) {
    int i;
    for ( i = 0; i < c; i++ ) {
        void * ptr = memArray[i];
        if (ptr == p) {
            int size = memArraySize[i];
            memArray[i] = NULL;
            memArraySize[i] = 0;
            printf("free: %p %d\n", p, size);
            total_freed += size;
        }
    }
    free ( p );
}

void printMemHelper() {
    current_total = total_allocated - total_freed;
    printf("Total Memory Allocated: %d\n", total_allocated );
    printf("Total Memory Freed    : %d\n", total_freed );
    printf("Total Memory Current  : %d\n", current_total );
}
