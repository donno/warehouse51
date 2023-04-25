as-lzf
======
An implementation of the LZF decompression algorithm in AssemblyScript.

This implementation is licensed under the terms of the ISC license.

Background
----------
I was unable to find a good description of the LZF algorithm itself, so mostly
this was based on a combination of Python, Rust and C implementation, the
latter was developed by Marc Alexander Lehmann. It was only when writing up
this email after getting the decompressor to work that I discovered
the C sharp implementation of the LZF by Oren J. Maurice  which likely would
have made an ideal point for a transcribing to AssemblyScript.

TODO
----
1. Complete the tests by decompressing the whole file.
2. Implement compression
3. Spin this off to its own repository and publish to NPM.