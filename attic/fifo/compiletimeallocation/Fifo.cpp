
// This is Demo.cpp
#include "Fifo.hpp"

#include <stdio.h>
#include <stdint.h>

int main() {
    Fifo<uint8_t, 12> fifo;
    Fifo<uint8_t, 20> fifo2;
    fifo.put(5);
    fifo2.put(5);
    
    if (!fifo.empty()) {
	//if (fifo == static_cast<Fifo<uint8_t, uint8_t> >(fifo2)) {
 	printf("%d\n", fifo.get());
    }
}
