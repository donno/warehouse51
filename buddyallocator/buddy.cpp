
#include "buddy.hpp"
#include "buddyallocator.hpp"

#include <vector>

// Ideally this would be iostreams but MSVC new up the locale in
// basic_streambuf under MSVC 2015.
#include <stdio.h>

// Check the allocators work.
std::size_t memory = 0;
std::size_t alloc = 0;

#ifdef _PREFAST_
_Ret_maybenull_ _Success_(return != NULL) _Post_writable_byte_size_(s)
#endif
__declspec(allocator) void* operator new(std::size_t s, const std::nothrow_t&) noexcept
{
    memory += s;
    ++alloc;
    void* result = malloc(s);
    return result;
}

void  operator delete(void* p) noexcept
{
    --alloc;
    free(p);
}

void memuse()
{
  printf("memory = %zu : alloc = %zu\n", memory, alloc);
}

#ifdef USE_VECTOR
template <class T>
using BuddyBackedVector = std::vector<T, donno::buddy_allocator<T>>;

int main2()
{
  BuddyBackedVector<char> numbers = {1, 5, 6};
  numbers.push_back(6);
  numbers.resize(5, 5);
  memuse(); // memory = 93 : alloc = 10
  numbers.push_back(6);
  numbers.resize(5, 5);
  memuse();
  return 0;
}
#endif

#include <cassert>

using namespace donno;

namespace
{
  // for_each element thanks to http://stackoverflow.com/a/6894436.
  template<std::size_t I = 0, typename FuncT, typename... Tp>
  inline typename std::enable_if<I == sizeof...(Tp), void>::type
  for_each(const std::tuple<Tp...>&, const std::tuple<Tp...>&, FuncT) {}

  template<std::size_t I = 0, typename FuncT, typename... Tp>
  inline typename std::enable_if<I < sizeof...(Tp), void>::type
  for_each(const std::tuple<Tp...>& t,
           const std::tuple<Tp...>& s, FuncT f)
  {
    f(std::get<I>(t), std::get<I>(s));
    for_each<I + 1, FuncT, Tp...>(t, s, f);
  }
  
  template<std::size_t I = 0, typename FuncT, typename... Tp>
  inline typename std::enable_if<I == sizeof...(Tp), void>::type
  for_each_if(std::tuple<Tp...>&, std::tuple<Tp...>&, FuncT) {}

  template<std::size_t I = 0, typename FuncT, typename... Tp>
  inline typename std::enable_if<I < sizeof...(Tp), void>::type
  for_each_if(std::tuple<Tp...>& t,
              std::tuple<Tp...>& s, FuncT f)
  {
    // If f returns true it will stop looking.
    //
    // Make this a specialisation of for_each, such that if the return type
    // of f is a bool then terminate if its true.
    if (f(I, std::get<I>(t), std::get<I>(s))) return;
    for_each_if<I + 1, FuncT, Tp...>(t, s, f);
  }

}

void Buddy::Visualise() const
{
  printf("Buddy - total size = %zu\n", largest_block_size);
  printf("  free space = %zu\n", free_space);

  const auto showBlock = [](const auto& was_split, const auto& was_allocated)
  {
    constexpr std::size_t width = 32; // The number of chars in the output.
    char buffer[width + 3];
    std::fill_n(buffer + 1, width, ' ');
    buffer[width] = '#';
    buffer[width + 1] = '\0';
    const auto divisions = was_split.size();
    const auto division_size = width / divisions;
    for (std::size_t i = 0, j = 0; i < width; i += division_size, ++j)
    {
      buffer[i] = '|'; // was_allocated
      if (was_allocated[j])
      {
        buffer[i + division_size / 2] = 'A';
      }
      else
      {     
        buffer[i + division_size / 2] = was_split[j] ? 'S' : 'F';
      }
    }
    buffer[0] = '#';
    printf("%4zu %s\n", largest_block_size / was_split.size(), buffer);
  };

  for_each(free, allocated, showBlock); 
}

#ifdef WORKING
// Mark a region as allocated.
template<std::size_t Level, typename T>
void MarkAllocated(T& allocated, std::size_t begin, std::size_t end)
{
  auto& is_allocated = std::get<Level>(allocated);
  for (; begin < end; ++begin)
  {
    is_allocated[begin] = true;
  }

  //assert(begin == 0 && "NYI: Must be the first block");
  //MarkAllocated<Level + 1>(allocated, 0, end * 2);
  if (Level == 2)
  {
    MarkAllocated<3>(allocated, 0, 4);
  }
  else if (Level == 3)
  {
    MarkAllocated<4>(allocated, 0, 8);
  }
  else if (Level == 4)
  {
    // Assert there is no 5 level.
  }
  else
  {
    assert(false && "NYI");
  }
}
#else
// This new version is a work in progress.

template<std::size_t I = 0, typename... Tp>
inline typename std::enable_if<I == sizeof...(Tp), void>::type
MarkAllocated(std::tuple<Tp...>&, std::size_t, std::size_t) {}

template<std::size_t Level, typename... Tp>
inline typename std::enable_if<Level < sizeof...(Tp), void>::type
MarkAllocated(std::tuple<Tp...>& allocated, std::size_t begin, std::size_t end)
{
  auto& is_allocated = std::get<Level>(allocated);
  for (auto i = begin; i < end; ++i)
  {
    is_allocated[i] = true;
  }

  // Adjust the begin and end for the next level.
  assert(begin == 0 && "Non-zero begin not supported yet.");
  MarkAllocated<Level + 1, Tp...>(allocated, begin, end + end);
}
#endif

void Buddy::allocate(std::size_t size)
{
  if (largest_block_size < size) throw std::bad_alloc();

  // Determine how much space is need by rounding up size to the next largest
  // block size.
  const auto remainder = size % smallest_block_size;
  if (remainder != 0)
  {
    size += smallest_block_size - remainder;
  }

  if (free_space < size)
  {
    throw std::bad_alloc();
  }
  
  // Determine which level.
  // Block indices
  // for 1024 we need to use level 0 and they all need to be none.
  printf("Need to allocate %zubytes (post-rounding up)\n", size);
  
  // Find a split, if not split it.
  // TODO...
  auto& was_split = std::get<0>(free);
  
  const bool old = false;
  if (was_split.none())
  {
    puts("  Nothing has been allocated so all the space is free.");
    // Trversal each level looking for the size required and splitting each
    // block into a smaller block.
    for_each_if(free, allocated,
                [=](std::size_t block_level, auto& was_split, auto& was_allocated)
    {
      if (largest_block_size / was_split.size() == size)
      {
        was_allocated[0] = true;
        assert(was_split[0] == false && "The block to allocate can not have been split.");

        // Mark all the smaller blocks that occupy the same address space as
        // this block as also being allocated.

        // TODO: This requires a function that can determine the indices into the 
        // allocated set below us.
        //
        // In this special case the first index is 0.
        //
        // For a 256-byte block:
        // - It should be 0, 1 for the 128-byte block below
        // - It should be 0, 1, 2, 3 for the 64-byte block below
        printf("  Allocating a block level: %zu\n", block_level);

        if (block_level == 1)
        {
          MarkAllocated<2>(allocated, 0, 2);
        }
        else
        {
          assert(false && "NYI");
        }
        
        return true;
      }
      else
      {
        was_split[0] = true;
      }
      return false;
    });
  }
  else if (old)
  {
    // Find if there are any free blocks of the given size.
    // This requires a different algorithm.
    // Consider:
    //   0   |  1
    //   0 1 | 2 3
    // 
    // If 1 is split then we need to look at 2 and 3 in the next level.

    // Consideration: This may be able cheat, if we marked all smaller blocks
    // as having been allocated if the block above has not been split we can
    // search faster. (This could be at the cost of some other operation).

    // Todo handle this manually.
    for (std::size_t i = 0; i < was_split.size(); ++i)
    {
      if (was_split[i])
      {
        auto& was_split_next = std::get<1>(free);
        if (was_split_next[i])
        {
          auto& was_split_next_next = std::get<2>(free);
          // TODO calucate the start properly
          if (was_split_next_next[0])
          {
            auto& was_allocated = std::get<3>(allocated);
            printf("Size %zu\n", largest_block_size / was_allocated.size());
            if (!was_allocated[0])
            {
              was_allocated[0] = true;
              break;
            }
            else if (!was_allocated[1])
            {
              was_allocated[1] = true;
              break;
            }
            else
            {
              // This block was full.
            }
          }

          if (was_split_next_next[1])
          {
            assert(false && "not yet implemented");
          }

          auto& was_allocated_next_next = std::get<2>(allocated);
          was_allocated_next_next[4] = true;
          /*if (was_split_next[i])
          {
            auto& was_split_next_next = std::get<2>(free);

          }*/
        }

        if (was_split_next[i + 1])
        {
          puts("second branch split");
          assert(false && "not yet implemented");
        }
      }
    }
  }
  else
  {
    // Determine if all the blocks are taken.

    // TODO: Determine which level to look at based on the size.

    assert(false);
    //


    //switch (
    //std::allocate_shared


    // Find which block is free, then split the blocks above it.

    
  }
  
  //freeSpace -= size;
}

int main3()
{
  Buddy buddy;
  printf("Size of the Buddy: %zu (storage: %zu, book keeping: %zu)\n",
         sizeof(Buddy),
         buddy.AvailableFreeSpace(), 
         sizeof(Buddy) - buddy.AvailableFreeSpace());
  printf("Free: %zu\n", buddy.AvailableFreeSpace());
  assert(buddy.AvailableFreeSpace() == 1024);
  
  printf("Size of a bitset: %zu\n", sizeof(std::bitset<6>));
  try
  {
    buddy.allocate(2000);
    assert(false && "The allocator is smaller than 2000 bytes");
  }
  catch (const std::bad_alloc&)
  {
    puts("Sucessfully throw a bad_alloc when required.");
  }
  
  buddy.Visualise();
  
  buddy.allocate(34);

  printf("Free: %zu\n", buddy.AvailableFreeSpace());
  //
  assert(buddy.AvailableFreeSpace() == (1024 - 32 - 32));  
  
  buddy.Visualise();
  buddy.allocate(34);
  buddy.Visualise();
  buddy.allocate(34);
  buddy.Visualise();
  try
  {
    buddy.allocate(1000);
    assert(false && "1000 bytes can only be allocated if the entire thing is "
                    "free");
  }
  catch (const std::bad_alloc&)
  {
    puts("Sucessfully throw a bad_alloc when required.");
  }

  // Test that every 32-byte block can be allocated.
  {
    Buddy fillBuddy;
    assert(fillBuddy.AvailableFreeSpace() == 1024);
    while (fillBuddy.AvailableFreeSpace() / 32 > 0)
    {
      fillBuddy.allocate(32);
    }
    assert(fillBuddy.AvailableFreeSpace() == 0);
    printf("Free: %zu == 0\n", fillBuddy.AvailableFreeSpace());
    fillBuddy.Visualise();
  }

  return 0;  
}

#ifdef HAS_CPP14_CONSTEXPR
// Computes how many many levels there are based on the largest and smallest
// size of a block.
constexpr auto level_count(std::size_t largest_block_size,
                           std::size_t smallest_block_size)
{
  unsigned short count{ 0 };
  for (auto size = largest_block_size; size > smallest_block_size; size /= 2)
  {
    ++count;
  }
  return count;
}
#else
// Computes how many many levels there are based on the largest and smallest
// size of a block.
constexpr short level_count(std::size_t largest_block_size,
                            std::size_t smallest_block_size)
{
  return (largest_block_size == smallest_block_size)
    ? 0
    : 1 + level_count(largest_block_size / 2, smallest_block_size);
}

#endif

int main()
{
  static_assert(level_count(1024, 32) == 5, "level_count() broken");

  Buddy buddy;
  assert(buddy.AvailableFreeSpace() == 1024);
  buddy.allocate(256);
  buddy.Visualise();
  buddy.allocate(256);
  buddy.Visualise();

  return 0;
}