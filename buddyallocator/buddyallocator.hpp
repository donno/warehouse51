// A C++ memory allocator that uses a technique called "bunny memory allocation."
// See https://en.wikipedia.org/wiki/Buddy_memory_allocation 
// This is mainly an experiemnt to write a minimumal C++11 allocator. 

#include <cstddef>

namespace donno
{
  // The goal is for this structure to model the concept of an allocator.
  // http://en.cppreference.com/w/cpp/concept/Allocator
  // TODO: Add tests for ensuring the std::allocator_traits can be used on the
  // type to provide suitable defaults.
  template <typename T>
  struct buddy_allocator {
    typedef T value_type;
    buddy_allocator() = default;
    buddy_allocator(const buddy_allocator&) = default;
    template<class U> buddy_allocator(const buddy_allocator<U>& other);
    buddy_allocator& operator=(const buddy_allocator&) = delete;

    T* allocate(std::size_t n);
    void deallocate(T* p, std::size_t n);

    alignas(alignof(T)) char buffer[1024];
  };

  template <class T, class U>
  bool operator==(const buddy_allocator<T>&, const buddy_allocator<U>&);
  template <class T, class U>
  bool operator!=(const buddy_allocator<T>&, const buddy_allocator<U>&);
}

// Implementation

#include <memory>

template <class T>
T* donno::buddy_allocator<T>::allocate(std::size_t)
{
  return buffer;
}

template <class T>
void donno::buddy_allocator<T>::deallocate(T*, std::size_t)
{
  //::operator delete(p);
  // TODO
}