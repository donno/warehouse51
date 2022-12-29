
// This is Fifo.hpp
#ifndef _FILE_HPP
#define _FILE_HPP
#include <stdlib.h>

template <typename _Type, typename _CapacityType>
class Fifo {
  volatile _Type read;
  volatile _Type write;
  volatile _CapacityType unconsumed;
  _CapacityType capacity;
  _Type* buffer;

  //unsigned long x;
public:
  Fifo(const _CapacityType capacity);
  ~Fifo();

  operator bool() const { return this->unconsumed == 0; }
  bool empty() const { return this->unconsumed == 0; }
  _Type get();
  void put(const _Type& p);
};

template <typename _Type, typename _CapacityType>
Fifo<_Type, _CapacityType>::Fifo(const _CapacityType capacity) {
  this->read = 0;
  this->write = 0;
  this->unconsumed = 0;
  this->capacity = capacity - 1;
  this->buffer = static_cast<_Type*>(malloc(sizeof(_Type) * capacity));
}

template <typename _Type, typename _CapacityType>
Fifo<_Type, _CapacityType>::~Fifo() {
  free(this->buffer);
}

template <typename _Type, typename _CapacityType>
_Type Fifo<_Type, _CapacityType>::get() {
  this->read = this->read & this->capacity;
  --this->unconsumed;
  return this->buffer[this->read++];
}

template <typename _Type, typename _CapacityType>
void Fifo<_Type, _CapacityType>::put(const _Type& p) {
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
