// Created April 2012
#include <list>

template <typename Ty>
class Cache
{
public:
  typedef typename std::list<Ty>::const_iterator const_iterator;
  typedef typename Ty value_type;

  const_iterator begin() const { return myData.begin(); }
  const_iterator end() const { return myData.end(); }

  void Flush();

  bool IsFull() const;


  void SetStartsAt(int StartsAt) { myStartsAt = StartsAt; }
  int StartsAt() const;
  int EndsAt() const;
  int Size() const { return ourSize; }

  void AddToStart(value_type Value);
  void AddToEnd(value_type Value);

private:
  int myStartsAt;

  std::list<Ty> myData;

  static int ourSize;
  // The size of the cache (ie the number of elements that can be stored in the
  // cache.
};

template <typename Ty>
int Cache<Ty>::ourSize = 2;

template <typename Ty>
void Cache<Ty>::Flush()
{
  myData.clear();
  myStartsAt = 0;
}

template <typename Ty>
bool Cache<Ty>::IsFull() const
{
  return myData.size() == ourSize;
}

template <typename Ty>
int Cache<Ty>::StartsAt() const
{
  return myStartsAt;
}

template <typename Ty>
int Cache<Ty>::EndsAt() const
{
  return myStartsAt + myData.size();
}

template <typename Ty>
void Cache<Ty>::AddToStart(value_type Value)
{
  if (myData.size() == ourSize)
  {
    // Push off the element at the end.
    myData.pop_back();
  }

  myData.push_front(Value);
  --myStartsAt;
}

template <typename Ty>
void Cache<Ty>::AddToEnd(value_type Value)
{
  if (myData.size() == ourSize)
  {
    // Push off the element at the start.
    myData.pop_front();
    ++myStartsAt;
  }

  myData.push_back(Value);
}

#include <iostream>
#include <functional>
#include <algorithm>

template<class T> struct print : public std::unary_function<T, void>
{
  print(std::ostream& out) : os(out) {}
  void operator() (T x) { os << x << ' '; }
  std::ostream& os;
};


void CacheGoto(int NewStart, Cache<char>* Cache)
{
  const int difference = NewStart - Cache->StartsAt();

  // Determine if the whole cache is going to be wiped.
  if (abs(difference) > Cache->Size())
  {
    // The entire cache is going to be blown away so just do it.
    Cache->Flush();
    Cache->SetStartsAt(NewStart);
    // Keep adding pages to the end of the cache till we get there.
    // This will remove remove the pages at the start.
    for (char startPopulating = 'a' + NewStart; !Cache->IsFull(); ++startPopulating)
    {
      Cache->AddToEnd( startPopulating );
    }
  }
  else if (difference < 0)
  {
    char startPopulating = 'a' + Cache->StartsAt() - 1;

    while (Cache->StartsAt() > NewStart)
    {
      Cache->AddToStart( startPopulating-- );
    }
  }
  else
  {
    // Calculate the distance from the end of the cache to th
    char startPopulating = 'a' + Cache->StartsAt() + difference;

    // Keep adding pages to the end of the cache till we get there.
    // This will remove remove the pages at the start.
    while (Cache->StartsAt() < NewStart)
    {
      Cache->AddToEnd( startPopulating++ );
    }
  }
}

int main()
{
  Cache<char> cache;

  // Populate cache.
  // Cache intally starts at 0.
  cache.Flush();

  for (char c = 'a'; !cache.IsFull(); ++c)
  {
    cache.AddToEnd(c);
  }

  std::cout << "Before: ";
  std::for_each(cache.begin(), cache.end(), print<char>(std::cout));
  std::cout << std::endl;

  // Add another one.
  cache.AddToEnd( 'a' + cache.EndsAt() );

  std::cout << "After: ";
  std::for_each(cache.begin(), cache.end(), print<char>(std::cout));
  std::cout << std::endl;

  std::cout << "Cache starts at " << cache.StartsAt() << ": ";
  CacheGoto(6, &cache);
  std::for_each(cache.begin(), cache.end(), print<char>(std::cout));
  std::cout << std::endl << "It now starts at " << cache.StartsAt() << std::endl;


  std::cout << "Cache starts at " << cache.StartsAt() << ": ";
  CacheGoto(1, &cache);
  std::for_each(cache.begin(), cache.end(), print<char>(std::cout));
  std::cout << std::endl << "It now starts at " << cache.StartsAt() << std::endl;

  CacheGoto(19, &cache);
  std::for_each(cache.begin(), cache.end(), print<char>(std::cout));
  std::cout << std::endl << "It now starts at " << cache.StartsAt() << std::endl;

  return 0;
}