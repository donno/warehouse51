
// This is Fifo.hpp
#ifndef _FILE_HPP
#define _FILE_HPP
#include <stdlib.h>

template <typename Type, size_t Capacity>
class Fifo {
  volatile Type read;
  volatile Type write;
  volatile size_t unconsumed;
  size_t capacity;
  Type buffer[Capacity];

public:
  Fifo();

  operator bool() const { return this->unconsumed == 0; }
  bool empty() const { return this->unconsumed == 0; }
  Type get();
  void put(const Type& p);
};

template <typename Type, size_t Capacity>
Fifo<Type, Capacity>::Fifo()
    : read(0),
      write(0),
      unconsumed(0),
      capacity(Capacity - 1)
{
}

template <typename Type, size_t Capacity>
Type Fifo<Type, Capacity>::get() {
  this->read = this->read & this->capacity;
  --this->unconsumed;
  return this->buffer[this->read++];
}

template <typename Type, size_t Capacity>
void Fifo<Type, Capacity>::put(const Type& p) {
  if (this->unconsumed > this->capacity) {
    return;
  }
  this->write = this->write & this->capacity;
  this->buffer[this->write++] = p;
  ++this->unconsumed;
}

#endif

// This is Fifo.cpp
/*
#include <stdlib.h>
#include "Fifo.hpp"

Fifo::Fifo(const uint8_t capacity) {
  this->read = 0;
  this->write = 0;
  this->unconsumed = 0;
  this->capacity = capacity - 1;
  this->buffer = static_cast<uint8_t*>(malloc(capacity));
}

uint8_t Fifo::get() {
  this->read = this->read & this->capacity;
  this->unconsumed--;
  return this->buffer[this->read++];
}

void Fifo::put(const uint8_t p) {
  if (this->unconsumed > this->capacity) {
    return;
  }
  this->write = this->write & this->capacity;
  this->buffer[this->write++] = p;
  this->unconsumed++;
}

Fifo::~Fifo() {
  free(this->buffer);
}


// This is Demo.cpp
#include <stdio.h>
#include "Fifo.hpp"
int main() {
  Fifo fifo(10);
  fifo.put(5);
  if (!fifo.em  pty()) {
    printf("%u\n", fifo.get());
  }
}
*/
