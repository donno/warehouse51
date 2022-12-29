#ifndef DONNO_BUDDY_HPP
#define DONNO_BUDDY_HPP
//===----------------------------------------------------------------------===//
// Buddy - A memory manager and allocator.
//===----------------------------------------------------------------------===//

#include <bitset>
#include <tuple>
#include <utility>

namespace donno
{
  // The metaprogramming namespace provides some handy functions used to
  // generate some types used by Buddy.
  namespace metaprogramming
  {
    // Makes an index sequence with the powers of two from another sequence.
    //
    // Given the sequence [0, 1, 2] returns [2, 4, 8]
    template<size_t ...power>
    constexpr auto power_of_two(std::index_sequence<power...>)
    {
      return std::index_sequence<(1 << (power + 1))...>{};
    }

    // Generate a tuple of std::tuple<std::bitset<I>, ...> where I comes from an
    // index_sequence sequence.
    template<size_t ...index>
    constexpr auto make_tuple_of_bitsets(std::index_sequence<index...>)
    {
      return std::tuple<std::bitset<index>...>{};
    }
  }

  // Buddy uses the buddy memory allocation algorithm which starts off with a
  // single large block of memory and divides it into smaller blocks if only
  // a small block needs to be allocated
  class Buddy
  {
    // TODO: Automatically generate the 5 below from
    // [largest|smallest]_block_size (see level_count() for how).
    using block_index_sequence = std::make_integer_sequence<std::size_t, 5>;
    using block_count_sequence =
      decltype(metaprogramming::power_of_two(block_index_sequence{}));

    static constexpr std::size_t largest_block_size = 1024;
    static constexpr std::size_t smallest_block_size = 32;
    char buffer[largest_block_size];
    std::size_t free_space = largest_block_size;

    // Define a data structure for keeping track of information about a block.
    //
    // This is like: typedef tuple<bitset<2>, bitset<4>, ...> metadata_t.
    typedef decltype(metaprogramming::make_tuple_of_bitsets(block_count_sequence{}))
      metadata_t;

    typedef std::tuple<
      std::bitset<2>,
      std::bitset<4>,
      std::bitset<8>,
      std::bitset<16>,
      std::bitset<32>> metadata_t;

    metadata_t free; // A false means free and true means it has been split.
    metadata_t allocated; // A false means free and true means its been allocated.
                          // free[i] and allocated[i] can't both be true.   

    // Returns the size of a block at a given level.
    // Level 0 will be equal to size
    // Level 1 will be equal to size / 2
    // Level 2 will be equal to size / 4 and so forth.
    // ...
    // The level will be equal to smallest_block_size.
    template <std::size_t Level>
    std::size_t size_of_block() const
    {
      return size / std::get<Level>(free).size();
    }

  public:
    std::size_t AvailableFreeSpace() const { return free_space; };

    void Visualise() const;

    // Allocates a block large enough to fit size.
    // 
    // In practice 'size' is rounded up to the nearest 2^k or
    // smallest_block_size.
    //
    // Throws std::bad_alloc if it can't allocate a block large enough.
    void allocate(std::size_t size);
  };
}

#endif
