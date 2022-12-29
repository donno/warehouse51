#include <stdio.h>

unsigned long fib (int n) {
    unsigned long last       = 1;
    unsigned long secondlast = 0;
    for (n = n - 1; n > 0; --n) {
        last = last + secondlast;
        secondlast = last - secondlast  ;
    }
    return last;
}

int main(){
    printf("fib(20): %lu", fib(20));
    return 0;
}