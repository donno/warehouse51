// The entry file of your WebAssembly module.

export function add(a: i32, b: i32): i32 {
  return a + b;
}

export function decompress(input: Uint8Array, max_length: i32): Uint8Array {
  var output = new Uint8Array(max_length);

  var inputIndex: i32 = 0;
  var outputIndex: i32 = 0;

  do {
    var ctrl = input[inputIndex] as u32;
    ++inputIndex;

    if (ctrl < (1 << 5)) {
      // Literal run
      ctrl++;

      if (outputIndex + ctrl > max_length) {
        throw new Error("Buffer was too small");
      }

      if (inputIndex + ctrl > input.length) {
        console.log(inputIndex.toString());
        throw new Error("Data is corrupted.");
      }

      do {
        output[outputIndex] = input[inputIndex];
        ++outputIndex;
        ++inputIndex;
      }
      while (--ctrl);
    }
    else {
      // back reference
      var len = (ctrl >> 5) as u32;
      var referenceOffset = outputIndex - ((ctrl & 0x1f) << 8) - 1;

      if (inputIndex >= input.length) {
        throw new Error("Data is corrupted.");
      }

      if (len == 7) {
        len += input[inputIndex];
        ++inputIndex;

        if (inputIndex >= input.length) {
          throw new Error("Data is corrupted.");
        }
      }

      referenceOffset -= input[inputIndex];
      ++inputIndex;

      if (outputIndex + len + 2 > max_length) {
        throw new Error("Buffer was too small");
      }

      // Missing error handling here.
      if (referenceOffset < 0) {
        throw new Error("Data is corrupted.");
      }

      output[outputIndex] = output[referenceOffset];
      ++outputIndex;
      ++referenceOffset;

      output[outputIndex] = output[referenceOffset];
      ++outputIndex;
      ++referenceOffset;

      do {
        output[outputIndex] = output[referenceOffset];
        ++outputIndex;
        ++referenceOffset;
      }
      while (--len);
    }
  }
  while (inputIndex < input.length);

  return output;
}
