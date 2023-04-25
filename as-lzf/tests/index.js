import assert from "assert";
import { add, decompress } from "../build/debug.js";
import { readFile, createReadStream } from 'node:fs';

// The file has the magic number with some extra metadata that decompress.
// doesn't handle.
//
// For example a lzf file consits of blocks in the following format:
// "ZV\0" 2-byte-usize <uncompressed data>
// "ZV\1" 2-byte-csize 2-byte-usize <compressed data>
// "ZV\2" 4-byte-crc32-0xdebb20e3 (NYI)
//
// At the moment dealing with this is not part of the library.
//
// export function decompress_file(file) {
//     const reader = new FileReader();
//     reader.onload = (evt) => {
//         console.log(evt.target.result);
//     };
//     reader.readAsArrayBuffer(file);
// }

assert.strictEqual(add(1, 2), 3);

readFile("tests/pg19221.txt.lzf", (err, data) => {
    if (err) {
        console.error(err);
        return;
    }

    assert.strictEqual(data[0], 'Z'.charCodeAt(0));
    assert.strictEqual(data[1], 'V'.charCodeAt(0));
    assert.strictEqual(data[2], 1); // Type 1.

    var compressedSize = data.readUInt16BE(3);
    var uncompressedSize = data.readUInt16BE(5);
    assert.strictEqual(compressedSize, 35671);
    assert.strictEqual(uncompressedSize, 65535); // 520,767

    // The file is encoded as blocks of size: compressedSize
    // The file is encoded as blocks?
    var result = decompress(data.slice(7, compressedSize + 7), uncompressedSize);

    // Compare result with the first uncompressedSize of the uncompressed
    // version (pg19221.txt).

    const stream = createReadStream(
        "tests/pg19221.txt", { start: 0, end: uncompressedSize - 1 });
    stream.on("data", chunk => {
        assert.deepStrictEqual(result, new Uint8Array(chunk));
    });

    var nextBlockStart = compressedSize + 7;

    // Read the next part of the file.
    assert.strictEqual(data[nextBlockStart + 0], 'Z'.charCodeAt(0));
    assert.strictEqual(data[nextBlockStart + 1], 'V'.charCodeAt(0));
    assert.strictEqual(data[nextBlockStart + 2], 1); // Type 1.

    compressedSize = data.readUInt16BE(3);
    uncompressedSize = data.readUInt16BE(5);
    assert.strictEqual(compressedSize, 35671);
    assert.strictEqual(uncompressedSize, 65535);
});

readFile("tests/hello.txt.lzf", (err, data) => {
    if (err) {
        console.error(err);
        return;
    }

    assert.strictEqual(data[0], 'Z'.charCodeAt(0));
    assert.strictEqual(data[1], 'V'.charCodeAt(0));
    assert.strictEqual(data[2], 0); // Type 0.

    // The first one might be a sign that it is uncompressed. TODO.
    var compressedSize = data.readUInt16BE(3);
    var uncompressedSize = data.readUInt16BE(3);
    assert.strictEqual(uncompressedSize, "Hello world!\n".length)
    assert.strictEqual(data.slice(5).toString('utf8'), "Hello world!\n");
});

console.log("ok");