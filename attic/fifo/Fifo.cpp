
// This is Demo.cpp
#include "Fifo.hpp"

#include <stdio.h>
#include <stdint.h>

int main() {
  Fifo<uint8_t, uint8_t> fifo(10);
  Fifo<uint8_t, uint8_t> fifo2(20);
  fifo.put(5);
  fifo2.put(5);
  //if (!fifo.empty()) {
  if (fifo == static_cast<Fifo<uint8_t, uint8_t> >(fifo2)) {
    printf("%ub\n", fifo.get());
  }
}
