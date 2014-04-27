//===----------------------------------------------------------------------===//
//
// NAME         : CollatzGenerator
// NAMESPACE    : Global namespace.
// PURPOSE      : Provided a way to iterate from a number down until it reaches
//                1 via the Collatz conjecture.
// COPYRIGHT    : (c) 2012 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provided a way to iterate over the sequence of numbers
//                from a starting point using the Collatz conjecture .
//
//                The Collatz conjecture is where if a number is even you
//                divided it by 2 else multiply it by 3 and add one until
//                you hopefully get to 1.
//
//                Supports ++, != and * operators.
//
//                Example usage:
//                  CollatzGenerator g(25);
//                  std::for_each(g.begin(), g.end(),
//                               [](unsigned long n){
//                                  std::cout << fib << " ";
//                                });
//                  Note: This will not print the terminating case ie 1.
//
//===----------------------------------------------------------------------===//

#include <iterator>

class CollatzGenerator :  public std::iterator<std::forward_iterator_tag,
                                               unsigned long>
{
  value_type n;

public:
  CollatzGenerator(const unsigned int startingNumber);

  CollatzGenerator& operator ++();

  value_type operator *() const { return n; }

  bool operator !=(const CollatzGenerator& That) const { return n != That.n; }

  // Starts at the beginning of the sequence.
  CollatzGenerator begin() const;

  // Defines the termination case.
  CollatzGenerator end() const;
};

//===----------------------------------------------------------------------===//

CollatzGenerator::CollatzGenerator(const unsigned int startingNumber)
: n(startingNumber)
{
}

CollatzGenerator& CollatzGenerator::operator ++() {
  n = ((n & 1) == 0) ? (n / 2) : (3 * n + 1);
  return *this;
}

CollatzGenerator CollatzGenerator::begin() const {
  return CollatzGenerator(n);
}

CollatzGenerator CollatzGenerator::end() const {
  return CollatzGenerator(1);
}

//===----------------------------------------------------------------------===//

#include <algorithm>
#include <iostream>

int main()
{
  CollatzGenerator g(25);

  std::cout << "Collatz conjecture: ";
  std::ostream_iterator<unsigned long> out(std::cout, " ");
  std::copy(g.begin(),g.end(), out);
  std::cout << 1 << std::endl;
  return 0;
}
//===----------------------------------------------------------------------===//
