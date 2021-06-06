//===----------------------------------------------------------------------===//
//
// NAME         : Fibonacci
// NAMESPACE    : Global namespace.
// PURPOSE      : Outputs the Fibonacci sequence.
// COPYRIGHT    : (c) 2015 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
//
//===----------------------------------------------------------------------===//

fn main() {
  let argument = std::env::args().nth(1);
  let mut x = 10;
  if !argument.is_none()
  {
    x = argument.unwrap().parse::<u32>().ok().unwrap_or_default();
  }

  // The seed values for the Fibonacci sequence are:
  // fib(0) = 0
  // fib(1) = 1
  //
  // With the recurrence relation defined as:
  // fib(n) = fib(n-1) + fib(n-2)
  let mut secondlast = 0;
  let mut last = 1;
  for _ in 0..x {
    last = last + secondlast;
    secondlast = last - secondlast;

    println!("{}", secondlast);
  }
}

//===----------------------------------------------------------------------===//

