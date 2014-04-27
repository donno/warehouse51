//===----------------------------------------------------------------------===//
//
// NAME         : FibonacciGenerator
// NAMESPACE    : Global namespace.
// PURPOSE      : Provided a way to iterate over the Fibonacci sequence.
// COPYRIGHT    : (c) 2012 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provided a way to iterate over the Fibonacci sequence.
//
//                Supports ++, != and * operators.
//
//                Example usage:
//                  FibonacciGenerator g;
//                  This will print out the first 10 Fibonacci numbers.
//                    std::for_each(g.begin(), g.end(10), [](int fib){
//                      std::cout << fib << " ";
//                      });
//
//                  This makes it incrediablity easy if you want to know
//                  the sum of the first 10 Fibonacci numbers.
//                    std::accumulate(g.begin(), g.end(10), 0)
//
//===----------------------------------------------------------------------===//

#include <iterator>

class FibonacciGenerator : public std::iterator<std::forward_iterator_tag,
                                                unsigned long>
{
  // last and secondlast is used in the calcuations.
  value_type last;
  value_type secondlast;

  // This is used for dealing with iteration.
  // n keeps track of the which 'n'-th fibiancii number we are up to.
  unsigned int n;

public:
  FibonacciGenerator();

  FibonacciGenerator& operator ++();

  // Returns the 'n-th' fibinacii number.
  value_type operator *() const { return secondlast; }

  bool operator !=(const FibonacciGenerator& That) const
  {
    return n != That.n;
  }

  // Starts at the beging of the sequence.
  FibonacciGenerator& begin();

  // Defines the termination case.
  FibonacciGenerator end(unsigned int nth) const;

};

//===----------------------------------------------------------------------===//

FibonacciGenerator::FibonacciGenerator()
: last(1), secondlast(0), n(0)
{
}

FibonacciGenerator& FibonacciGenerator::operator ++() {
  last = last + secondlast;
  secondlast = last - secondlast;
  ++n;
  return *this;
}

FibonacciGenerator& FibonacciGenerator::begin() {
  n = 0;
  return *this;
}

FibonacciGenerator FibonacciGenerator::end(unsigned int nth) const {
  FibonacciGenerator endFibonacci;
  endFibonacci.n = nth;
  return endFibonacci;
}

//===----------------------------------------------------------------------===//

#include <algorithm>
#include <iostream>
#include <numeric>

int main()
{
  FibonacciGenerator g;
  std::cout << "Fibonacci: ";
  std::ostream_iterator<FibonacciGenerator::value_type> out(std::cout, " ");
  std::copy(g.begin(), g.end(10), out);
  std::cout << std::endl;

  std::cout << "Sum of first 10 Fibonacci numbers: "
            << std::accumulate(g.begin(), g.end(10), 0)
            << std::endl;
  return 0;
}
//===----------------------------------------------------------------------===//
