//===----------------------------------------------------------------------===//
//
// NAME         : CollatzSequence
// PURPOSE      : Provided a way to iterate from a number down until it reaches
//                1 via the Collatz conjecture.
// COPYRIGHT    : (c) 2015 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
//
//===----------------------------------------------------------------------===//

struct CollatzSequence {
  value: u32,
}

impl Iterator for CollatzSequence {
  type Item = u32;
  fn next(&mut self) -> Option<u32> {
    if self.value == 1 {
      return None
    }

    self.value = if (self.value & 1) == 0 { self.value / 2 }
                 else { 3 * self.value + 1 };

    Some(self.value)
  }
}

fn main() {
  let sequence = CollatzSequence { value: 200 };
  for i in sequence {
    println!("{}", i);
  }
}

//===----------------------------------------------------------------------===//
