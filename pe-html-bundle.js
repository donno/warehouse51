(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){

},{}],2:[function(require,module,exports){
/*!
 * The buffer module from node.js, for the browser.
 *
 * @author   Feross Aboukhadijeh <feross@feross.org> <http://feross.org>
 * @license  MIT
 */

var base64 = require('base64-js')
var ieee754 = require('ieee754')
var isArray = require('is-array')

exports.Buffer = Buffer
exports.SlowBuffer = SlowBuffer
exports.INSPECT_MAX_BYTES = 50
Buffer.poolSize = 8192 // not used by this implementation

var kMaxLength = 0x3fffffff
var rootParent = {}

/**
 * If `Buffer.TYPED_ARRAY_SUPPORT`:
 *   === true    Use Uint8Array implementation (fastest)
 *   === false   Use Object implementation (most compatible, even IE6)
 *
 * Browsers that support typed arrays are IE 10+, Firefox 4+, Chrome 7+, Safari 5.1+,
 * Opera 11.6+, iOS 4.2+.
 *
 * Note:
 *
 * - Implementation must support adding new properties to `Uint8Array` instances.
 *   Firefox 4-29 lacked support, fixed in Firefox 30+.
 *   See: https://bugzilla.mozilla.org/show_bug.cgi?id=695438.
 *
 *  - Chrome 9-10 is missing the `TypedArray.prototype.subarray` function.
 *
 *  - IE10 has a broken `TypedArray.prototype.subarray` function which returns arrays of
 *    incorrect length in some situations.
 *
 * We detect these buggy browsers and set `Buffer.TYPED_ARRAY_SUPPORT` to `false` so they will
 * get the Object implementation, which is slower but will work correctly.
 */
Buffer.TYPED_ARRAY_SUPPORT = (function () {
  try {
    var buf = new ArrayBuffer(0)
    var arr = new Uint8Array(buf)
    arr.foo = function () { return 42 }
    return arr.foo() === 42 && // typed array instances can be augmented
        typeof arr.subarray === 'function' && // chrome 9-10 lack `subarray`
        new Uint8Array(1).subarray(1, 1).byteLength === 0 // ie10 has broken `subarray`
  } catch (e) {
    return false
  }
})()

/**
 * Class: Buffer
 * =============
 *
 * The Buffer constructor returns instances of `Uint8Array` that are augmented
 * with function properties for all the node `Buffer` API functions. We use
 * `Uint8Array` so that square bracket notation works as expected -- it returns
 * a single octet.
 *
 * By augmenting the instances, we can avoid modifying the `Uint8Array`
 * prototype.
 */
function Buffer (subject, encoding, noZero) {
  if (!(this instanceof Buffer))
    return new Buffer(subject, encoding, noZero)

  var type = typeof subject

  // Find the length
  var length
  if (type === 'number')
    length = +subject
  else if (type === 'string') {
    length = Buffer.byteLength(subject, encoding)
  } else if (type === 'object' && subject !== null) { // assume object is array-like
    if (subject.type === 'Buffer' && isArray(subject.data))
      subject = subject.data
    length = +subject.length
  } else {
    throw new TypeError('must start with number, buffer, array or string')
  }

  if (length > kMaxLength)
    throw new RangeError('Attempt to allocate Buffer larger than maximum ' +
      'size: 0x' + kMaxLength.toString(16) + ' bytes')

  if (length < 0)
    length = 0
  else
    length >>>= 0 // Coerce to uint32.

  var self = this
  if (Buffer.TYPED_ARRAY_SUPPORT) {
    // Preferred: Return an augmented `Uint8Array` instance for best performance
    /*eslint-disable consistent-this */
    self = Buffer._augment(new Uint8Array(length))
    /*eslint-enable consistent-this */
  } else {
    // Fallback: Return THIS instance of Buffer (created by `new`)
    self.length = length
    self._isBuffer = true
  }

  var i
  if (Buffer.TYPED_ARRAY_SUPPORT && typeof subject.byteLength === 'number') {
    // Speed optimization -- use set if we're copying from a typed array
    self._set(subject)
  } else if (isArrayish(subject)) {
    // Treat array-ish objects as a byte array
    if (Buffer.isBuffer(subject)) {
      for (i = 0; i < length; i++)
        self[i] = subject.readUInt8(i)
    } else {
      for (i = 0; i < length; i++)
        self[i] = ((subject[i] % 256) + 256) % 256
    }
  } else if (type === 'string') {
    self.write(subject, 0, encoding)
  } else if (type === 'number' && !Buffer.TYPED_ARRAY_SUPPORT && !noZero) {
    for (i = 0; i < length; i++) {
      self[i] = 0
    }
  }

  if (length > 0 && length <= Buffer.poolSize)
    self.parent = rootParent

  return self
}

function SlowBuffer (subject, encoding, noZero) {
  if (!(this instanceof SlowBuffer))
    return new SlowBuffer(subject, encoding, noZero)

  var buf = new Buffer(subject, encoding, noZero)
  delete buf.parent
  return buf
}

Buffer.isBuffer = function (b) {
  return !!(b != null && b._isBuffer)
}

Buffer.compare = function (a, b) {
  if (!Buffer.isBuffer(a) || !Buffer.isBuffer(b))
    throw new TypeError('Arguments must be Buffers')

  if (a === b) return 0

  var x = a.length
  var y = b.length
  for (var i = 0, len = Math.min(x, y); i < len && a[i] === b[i]; i++) {}
  if (i !== len) {
    x = a[i]
    y = b[i]
  }
  if (x < y) return -1
  if (y < x) return 1
  return 0
}

Buffer.isEncoding = function (encoding) {
  switch (String(encoding).toLowerCase()) {
    case 'hex':
    case 'utf8':
    case 'utf-8':
    case 'ascii':
    case 'binary':
    case 'base64':
    case 'raw':
    case 'ucs2':
    case 'ucs-2':
    case 'utf16le':
    case 'utf-16le':
      return true
    default:
      return false
  }
}

Buffer.concat = function (list, totalLength) {
  if (!isArray(list)) throw new TypeError('Usage: Buffer.concat(list[, length])')

  if (list.length === 0) {
    return new Buffer(0)
  } else if (list.length === 1) {
    return list[0]
  }

  var i
  if (totalLength === undefined) {
    totalLength = 0
    for (i = 0; i < list.length; i++) {
      totalLength += list[i].length
    }
  }

  var buf = new Buffer(totalLength)
  var pos = 0
  for (i = 0; i < list.length; i++) {
    var item = list[i]
    item.copy(buf, pos)
    pos += item.length
  }
  return buf
}

Buffer.byteLength = function (str, encoding) {
  var ret
  str = str + ''
  switch (encoding || 'utf8') {
    case 'ascii':
    case 'binary':
    case 'raw':
      ret = str.length
      break
    case 'ucs2':
    case 'ucs-2':
    case 'utf16le':
    case 'utf-16le':
      ret = str.length * 2
      break
    case 'hex':
      ret = str.length >>> 1
      break
    case 'utf8':
    case 'utf-8':
      ret = utf8ToBytes(str).length
      break
    case 'base64':
      ret = base64ToBytes(str).length
      break
    default:
      ret = str.length
  }
  return ret
}

// pre-set for values that may exist in the future
Buffer.prototype.length = undefined
Buffer.prototype.parent = undefined

// toString(encoding, start=0, end=buffer.length)
Buffer.prototype.toString = function (encoding, start, end) {
  var loweredCase = false

  start = start >>> 0
  end = end === undefined || end === Infinity ? this.length : end >>> 0

  if (!encoding) encoding = 'utf8'
  if (start < 0) start = 0
  if (end > this.length) end = this.length
  if (end <= start) return ''

  while (true) {
    switch (encoding) {
      case 'hex':
        return hexSlice(this, start, end)

      case 'utf8':
      case 'utf-8':
        return utf8Slice(this, start, end)

      case 'ascii':
        return asciiSlice(this, start, end)

      case 'binary':
        return binarySlice(this, start, end)

      case 'base64':
        return base64Slice(this, start, end)

      case 'ucs2':
      case 'ucs-2':
      case 'utf16le':
      case 'utf-16le':
        return utf16leSlice(this, start, end)

      default:
        if (loweredCase)
          throw new TypeError('Unknown encoding: ' + encoding)
        encoding = (encoding + '').toLowerCase()
        loweredCase = true
    }
  }
}

Buffer.prototype.equals = function (b) {
  if (!Buffer.isBuffer(b)) throw new TypeError('Argument must be a Buffer')
  if (this === b) return true
  return Buffer.compare(this, b) === 0
}

Buffer.prototype.inspect = function () {
  var str = ''
  var max = exports.INSPECT_MAX_BYTES
  if (this.length > 0) {
    str = this.toString('hex', 0, max).match(/.{2}/g).join(' ')
    if (this.length > max)
      str += ' ... '
  }
  return '<Buffer ' + str + '>'
}

Buffer.prototype.compare = function (b) {
  if (!Buffer.isBuffer(b)) throw new TypeError('Argument must be a Buffer')
  if (this === b) return 0
  return Buffer.compare(this, b)
}

// `get` will be removed in Node 0.13+
Buffer.prototype.get = function (offset) {
  console.log('.get() is deprecated. Access using array indexes instead.')
  return this.readUInt8(offset)
}

// `set` will be removed in Node 0.13+
Buffer.prototype.set = function (v, offset) {
  console.log('.set() is deprecated. Access using array indexes instead.')
  return this.writeUInt8(v, offset)
}

function hexWrite (buf, string, offset, length) {
  offset = Number(offset) || 0
  var remaining = buf.length - offset
  if (!length) {
    length = remaining
  } else {
    length = Number(length)
    if (length > remaining) {
      length = remaining
    }
  }

  // must be an even number of digits
  var strLen = string.length
  if (strLen % 2 !== 0) throw new Error('Invalid hex string')

  if (length > strLen / 2) {
    length = strLen / 2
  }
  for (var i = 0; i < length; i++) {
    var byte = parseInt(string.substr(i * 2, 2), 16)
    if (isNaN(byte)) throw new Error('Invalid hex string')
    buf[offset + i] = byte
  }
  return i
}

function utf8Write (buf, string, offset, length) {
  var charsWritten = blitBuffer(utf8ToBytes(string, buf.length - offset), buf, offset, length)
  return charsWritten
}

function asciiWrite (buf, string, offset, length) {
  var charsWritten = blitBuffer(asciiToBytes(string), buf, offset, length)
  return charsWritten
}

function binaryWrite (buf, string, offset, length) {
  return asciiWrite(buf, string, offset, length)
}

function base64Write (buf, string, offset, length) {
  var charsWritten = blitBuffer(base64ToBytes(string), buf, offset, length)
  return charsWritten
}

function utf16leWrite (buf, string, offset, length) {
  var charsWritten = blitBuffer(utf16leToBytes(string, buf.length - offset), buf, offset, length, 2)
  return charsWritten
}

Buffer.prototype.write = function (string, offset, length, encoding) {
  // Support both (string, offset, length, encoding)
  // and the legacy (string, encoding, offset, length)
  if (isFinite(offset)) {
    if (!isFinite(length)) {
      encoding = length
      length = undefined
    }
  } else {  // legacy
    var swap = encoding
    encoding = offset
    offset = length
    length = swap
  }

  offset = Number(offset) || 0

  if (length < 0 || offset < 0 || offset > this.length)
    throw new RangeError('attempt to write outside buffer bounds')

  var remaining = this.length - offset
  if (!length) {
    length = remaining
  } else {
    length = Number(length)
    if (length > remaining) {
      length = remaining
    }
  }
  encoding = String(encoding || 'utf8').toLowerCase()

  var ret
  switch (encoding) {
    case 'hex':
      ret = hexWrite(this, string, offset, length)
      break
    case 'utf8':
    case 'utf-8':
      ret = utf8Write(this, string, offset, length)
      break
    case 'ascii':
      ret = asciiWrite(this, string, offset, length)
      break
    case 'binary':
      ret = binaryWrite(this, string, offset, length)
      break
    case 'base64':
      ret = base64Write(this, string, offset, length)
      break
    case 'ucs2':
    case 'ucs-2':
    case 'utf16le':
    case 'utf-16le':
      ret = utf16leWrite(this, string, offset, length)
      break
    default:
      throw new TypeError('Unknown encoding: ' + encoding)
  }
  return ret
}

Buffer.prototype.toJSON = function () {
  return {
    type: 'Buffer',
    data: Array.prototype.slice.call(this._arr || this, 0)
  }
}

function base64Slice (buf, start, end) {
  if (start === 0 && end === buf.length) {
    return base64.fromByteArray(buf)
  } else {
    return base64.fromByteArray(buf.slice(start, end))
  }
}

function utf8Slice (buf, start, end) {
  var res = ''
  var tmp = ''
  end = Math.min(buf.length, end)

  for (var i = start; i < end; i++) {
    if (buf[i] <= 0x7F) {
      res += decodeUtf8Char(tmp) + String.fromCharCode(buf[i])
      tmp = ''
    } else {
      tmp += '%' + buf[i].toString(16)
    }
  }

  return res + decodeUtf8Char(tmp)
}

function asciiSlice (buf, start, end) {
  var ret = ''
  end = Math.min(buf.length, end)

  for (var i = start; i < end; i++) {
    ret += String.fromCharCode(buf[i] & 0x7F)
  }
  return ret
}

function binarySlice (buf, start, end) {
  var ret = ''
  end = Math.min(buf.length, end)

  for (var i = start; i < end; i++) {
    ret += String.fromCharCode(buf[i])
  }
  return ret
}

function hexSlice (buf, start, end) {
  var len = buf.length

  if (!start || start < 0) start = 0
  if (!end || end < 0 || end > len) end = len

  var out = ''
  for (var i = start; i < end; i++) {
    out += toHex(buf[i])
  }
  return out
}

function utf16leSlice (buf, start, end) {
  var bytes = buf.slice(start, end)
  var res = ''
  for (var i = 0; i < bytes.length; i += 2) {
    res += String.fromCharCode(bytes[i] + bytes[i + 1] * 256)
  }
  return res
}

Buffer.prototype.slice = function (start, end) {
  var len = this.length
  start = ~~start
  end = end === undefined ? len : ~~end

  if (start < 0) {
    start += len
    if (start < 0)
      start = 0
  } else if (start > len) {
    start = len
  }

  if (end < 0) {
    end += len
    if (end < 0)
      end = 0
  } else if (end > len) {
    end = len
  }

  if (end < start)
    end = start

  var newBuf
  if (Buffer.TYPED_ARRAY_SUPPORT) {
    newBuf = Buffer._augment(this.subarray(start, end))
  } else {
    var sliceLen = end - start
    newBuf = new Buffer(sliceLen, undefined, true)
    for (var i = 0; i < sliceLen; i++) {
      newBuf[i] = this[i + start]
    }
  }

  if (newBuf.length)
    newBuf.parent = this.parent || this

  return newBuf
}

/*
 * Need to make sure that buffer isn't trying to write out of bounds.
 */
function checkOffset (offset, ext, length) {
  if ((offset % 1) !== 0 || offset < 0)
    throw new RangeError('offset is not uint')
  if (offset + ext > length)
    throw new RangeError('Trying to access beyond buffer length')
}

Buffer.prototype.readUIntLE = function (offset, byteLength, noAssert) {
  offset = offset >>> 0
  byteLength = byteLength >>> 0
  if (!noAssert)
    checkOffset(offset, byteLength, this.length)

  var val = this[offset]
  var mul = 1
  var i = 0
  while (++i < byteLength && (mul *= 0x100))
    val += this[offset + i] * mul

  return val
}

Buffer.prototype.readUIntBE = function (offset, byteLength, noAssert) {
  offset = offset >>> 0
  byteLength = byteLength >>> 0
  if (!noAssert)
    checkOffset(offset, byteLength, this.length)

  var val = this[offset + --byteLength]
  var mul = 1
  while (byteLength > 0 && (mul *= 0x100))
    val += this[offset + --byteLength] * mul

  return val
}

Buffer.prototype.readUInt8 = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 1, this.length)
  return this[offset]
}

Buffer.prototype.readUInt16LE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 2, this.length)
  return this[offset] | (this[offset + 1] << 8)
}

Buffer.prototype.readUInt16BE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 2, this.length)
  return (this[offset] << 8) | this[offset + 1]
}

Buffer.prototype.readUInt32LE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 4, this.length)

  return ((this[offset]) |
      (this[offset + 1] << 8) |
      (this[offset + 2] << 16)) +
      (this[offset + 3] * 0x1000000)
}

Buffer.prototype.readUInt32BE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 4, this.length)

  return (this[offset] * 0x1000000) +
      ((this[offset + 1] << 16) |
      (this[offset + 2] << 8) |
      this[offset + 3])
}

Buffer.prototype.readIntLE = function (offset, byteLength, noAssert) {
  offset = offset >>> 0
  byteLength = byteLength >>> 0
  if (!noAssert)
    checkOffset(offset, byteLength, this.length)

  var val = this[offset]
  var mul = 1
  var i = 0
  while (++i < byteLength && (mul *= 0x100))
    val += this[offset + i] * mul
  mul *= 0x80

  if (val >= mul)
    val -= Math.pow(2, 8 * byteLength)

  return val
}

Buffer.prototype.readIntBE = function (offset, byteLength, noAssert) {
  offset = offset >>> 0
  byteLength = byteLength >>> 0
  if (!noAssert)
    checkOffset(offset, byteLength, this.length)

  var i = byteLength
  var mul = 1
  var val = this[offset + --i]
  while (i > 0 && (mul *= 0x100))
    val += this[offset + --i] * mul
  mul *= 0x80

  if (val >= mul)
    val -= Math.pow(2, 8 * byteLength)

  return val
}

Buffer.prototype.readInt8 = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 1, this.length)
  if (!(this[offset] & 0x80))
    return (this[offset])
  return ((0xff - this[offset] + 1) * -1)
}

Buffer.prototype.readInt16LE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 2, this.length)
  var val = this[offset] | (this[offset + 1] << 8)
  return (val & 0x8000) ? val | 0xFFFF0000 : val
}

Buffer.prototype.readInt16BE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 2, this.length)
  var val = this[offset + 1] | (this[offset] << 8)
  return (val & 0x8000) ? val | 0xFFFF0000 : val
}

Buffer.prototype.readInt32LE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 4, this.length)

  return (this[offset]) |
      (this[offset + 1] << 8) |
      (this[offset + 2] << 16) |
      (this[offset + 3] << 24)
}

Buffer.prototype.readInt32BE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 4, this.length)

  return (this[offset] << 24) |
      (this[offset + 1] << 16) |
      (this[offset + 2] << 8) |
      (this[offset + 3])
}

Buffer.prototype.readFloatLE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 4, this.length)
  return ieee754.read(this, offset, true, 23, 4)
}

Buffer.prototype.readFloatBE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 4, this.length)
  return ieee754.read(this, offset, false, 23, 4)
}

Buffer.prototype.readDoubleLE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 8, this.length)
  return ieee754.read(this, offset, true, 52, 8)
}

Buffer.prototype.readDoubleBE = function (offset, noAssert) {
  if (!noAssert)
    checkOffset(offset, 8, this.length)
  return ieee754.read(this, offset, false, 52, 8)
}

function checkInt (buf, value, offset, ext, max, min) {
  if (!Buffer.isBuffer(buf)) throw new TypeError('buffer must be a Buffer instance')
  if (value > max || value < min) throw new RangeError('value is out of bounds')
  if (offset + ext > buf.length) throw new RangeError('index out of range')
}

Buffer.prototype.writeUIntLE = function (value, offset, byteLength, noAssert) {
  value = +value
  offset = offset >>> 0
  byteLength = byteLength >>> 0
  if (!noAssert)
    checkInt(this, value, offset, byteLength, Math.pow(2, 8 * byteLength), 0)

  var mul = 1
  var i = 0
  this[offset] = value & 0xFF
  while (++i < byteLength && (mul *= 0x100))
    this[offset + i] = (value / mul) >>> 0 & 0xFF

  return offset + byteLength
}

Buffer.prototype.writeUIntBE = function (value, offset, byteLength, noAssert) {
  value = +value
  offset = offset >>> 0
  byteLength = byteLength >>> 0
  if (!noAssert)
    checkInt(this, value, offset, byteLength, Math.pow(2, 8 * byteLength), 0)

  var i = byteLength - 1
  var mul = 1
  this[offset + i] = value & 0xFF
  while (--i >= 0 && (mul *= 0x100))
    this[offset + i] = (value / mul) >>> 0 & 0xFF

  return offset + byteLength
}

Buffer.prototype.writeUInt8 = function (value, offset, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert)
    checkInt(this, value, offset, 1, 0xff, 0)
  if (!Buffer.TYPED_ARRAY_SUPPORT) value = Math.floor(value)
  this[offset] = value
  return offset + 1
}

function objectWriteUInt16 (buf, value, offset, littleEndian) {
  if (value < 0) value = 0xffff + value + 1
  for (var i = 0, j = Math.min(buf.length - offset, 2); i < j; i++) {
    buf[offset + i] = (value & (0xff << (8 * (littleEndian ? i : 1 - i)))) >>>
      (littleEndian ? i : 1 - i) * 8
  }
}

Buffer.prototype.writeUInt16LE = function (value, offset, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert)
    checkInt(this, value, offset, 2, 0xffff, 0)
  if (Buffer.TYPED_ARRAY_SUPPORT) {
    this[offset] = value
    this[offset + 1] = (value >>> 8)
  } else objectWriteUInt16(this, value, offset, true)
  return offset + 2
}

Buffer.prototype.writeUInt16BE = function (value, offset, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert)
    checkInt(this, value, offset, 2, 0xffff, 0)
  if (Buffer.TYPED_ARRAY_SUPPORT) {
    this[offset] = (value >>> 8)
    this[offset + 1] = value
  } else objectWriteUInt16(this, value, offset, false)
  return offset + 2
}

function objectWriteUInt32 (buf, value, offset, littleEndian) {
  if (value < 0) value = 0xffffffff + value + 1
  for (var i = 0, j = Math.min(buf.length - offset, 4); i < j; i++) {
    buf[offset + i] = (value >>> (littleEndian ? i : 3 - i) * 8) & 0xff
  }
}

Buffer.prototype.writeUInt32LE = function (value, offset, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert)
    checkInt(this, value, offset, 4, 0xffffffff, 0)
  if (Buffer.TYPED_ARRAY_SUPPORT) {
    this[offset + 3] = (value >>> 24)
    this[offset + 2] = (value >>> 16)
    this[offset + 1] = (value >>> 8)
    this[offset] = value
  } else objectWriteUInt32(this, value, offset, true)
  return offset + 4
}

Buffer.prototype.writeUInt32BE = function (value, offset, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert)
    checkInt(this, value, offset, 4, 0xffffffff, 0)
  if (Buffer.TYPED_ARRAY_SUPPORT) {
    this[offset] = (value >>> 24)
    this[offset + 1] = (value >>> 16)
    this[offset + 2] = (value >>> 8)
    this[offset + 3] = value
  } else objectWriteUInt32(this, value, offset, false)
  return offset + 4
}

Buffer.prototype.writeIntLE = function (value, offset, byteLength, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert) {
    checkInt(this,
             value,
             offset,
             byteLength,
             Math.pow(2, 8 * byteLength - 1) - 1,
             -Math.pow(2, 8 * byteLength - 1))
  }

  var i = 0
  var mul = 1
  var sub = value < 0 ? 1 : 0
  this[offset] = value & 0xFF
  while (++i < byteLength && (mul *= 0x100))
    this[offset + i] = ((value / mul) >> 0) - sub & 0xFF

  return offset + byteLength
}

Buffer.prototype.writeIntBE = function (value, offset, byteLength, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert) {
    checkInt(this,
             value,
             offset,
             byteLength,
             Math.pow(2, 8 * byteLength - 1) - 1,
             -Math.pow(2, 8 * byteLength - 1))
  }

  var i = byteLength - 1
  var mul = 1
  var sub = value < 0 ? 1 : 0
  this[offset + i] = value & 0xFF
  while (--i >= 0 && (mul *= 0x100))
    this[offset + i] = ((value / mul) >> 0) - sub & 0xFF

  return offset + byteLength
}

Buffer.prototype.writeInt8 = function (value, offset, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert)
    checkInt(this, value, offset, 1, 0x7f, -0x80)
  if (!Buffer.TYPED_ARRAY_SUPPORT) value = Math.floor(value)
  if (value < 0) value = 0xff + value + 1
  this[offset] = value
  return offset + 1
}

Buffer.prototype.writeInt16LE = function (value, offset, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert)
    checkInt(this, value, offset, 2, 0x7fff, -0x8000)
  if (Buffer.TYPED_ARRAY_SUPPORT) {
    this[offset] = value
    this[offset + 1] = (value >>> 8)
  } else objectWriteUInt16(this, value, offset, true)
  return offset + 2
}

Buffer.prototype.writeInt16BE = function (value, offset, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert)
    checkInt(this, value, offset, 2, 0x7fff, -0x8000)
  if (Buffer.TYPED_ARRAY_SUPPORT) {
    this[offset] = (value >>> 8)
    this[offset + 1] = value
  } else objectWriteUInt16(this, value, offset, false)
  return offset + 2
}

Buffer.prototype.writeInt32LE = function (value, offset, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert)
    checkInt(this, value, offset, 4, 0x7fffffff, -0x80000000)
  if (Buffer.TYPED_ARRAY_SUPPORT) {
    this[offset] = value
    this[offset + 1] = (value >>> 8)
    this[offset + 2] = (value >>> 16)
    this[offset + 3] = (value >>> 24)
  } else objectWriteUInt32(this, value, offset, true)
  return offset + 4
}

Buffer.prototype.writeInt32BE = function (value, offset, noAssert) {
  value = +value
  offset = offset >>> 0
  if (!noAssert)
    checkInt(this, value, offset, 4, 0x7fffffff, -0x80000000)
  if (value < 0) value = 0xffffffff + value + 1
  if (Buffer.TYPED_ARRAY_SUPPORT) {
    this[offset] = (value >>> 24)
    this[offset + 1] = (value >>> 16)
    this[offset + 2] = (value >>> 8)
    this[offset + 3] = value
  } else objectWriteUInt32(this, value, offset, false)
  return offset + 4
}

function checkIEEE754 (buf, value, offset, ext, max, min) {
  if (value > max || value < min) throw new RangeError('value is out of bounds')
  if (offset + ext > buf.length) throw new RangeError('index out of range')
  if (offset < 0) throw new RangeError('index out of range')
}

function writeFloat (buf, value, offset, littleEndian, noAssert) {
  if (!noAssert)
    checkIEEE754(buf, value, offset, 4, 3.4028234663852886e+38, -3.4028234663852886e+38)
  ieee754.write(buf, value, offset, littleEndian, 23, 4)
  return offset + 4
}

Buffer.prototype.writeFloatLE = function (value, offset, noAssert) {
  return writeFloat(this, value, offset, true, noAssert)
}

Buffer.prototype.writeFloatBE = function (value, offset, noAssert) {
  return writeFloat(this, value, offset, false, noAssert)
}

function writeDouble (buf, value, offset, littleEndian, noAssert) {
  if (!noAssert)
    checkIEEE754(buf, value, offset, 8, 1.7976931348623157E+308, -1.7976931348623157E+308)
  ieee754.write(buf, value, offset, littleEndian, 52, 8)
  return offset + 8
}

Buffer.prototype.writeDoubleLE = function (value, offset, noAssert) {
  return writeDouble(this, value, offset, true, noAssert)
}

Buffer.prototype.writeDoubleBE = function (value, offset, noAssert) {
  return writeDouble(this, value, offset, false, noAssert)
}

// copy(targetBuffer, targetStart=0, sourceStart=0, sourceEnd=buffer.length)
Buffer.prototype.copy = function (target, target_start, start, end) {
  var self = this // source

  if (!start) start = 0
  if (!end && end !== 0) end = this.length
  if (target_start >= target.length) target_start = target.length
  if (!target_start) target_start = 0
  if (end > 0 && end < start) end = start

  // Copy 0 bytes; we're done
  if (end === start) return 0
  if (target.length === 0 || self.length === 0) return 0

  // Fatal error conditions
  if (target_start < 0)
    throw new RangeError('targetStart out of bounds')
  if (start < 0 || start >= self.length) throw new RangeError('sourceStart out of bounds')
  if (end < 0) throw new RangeError('sourceEnd out of bounds')

  // Are we oob?
  if (end > this.length)
    end = this.length
  if (target.length - target_start < end - start)
    end = target.length - target_start + start

  var len = end - start

  if (len < 1000 || !Buffer.TYPED_ARRAY_SUPPORT) {
    for (var i = 0; i < len; i++) {
      target[i + target_start] = this[i + start]
    }
  } else {
    target._set(this.subarray(start, start + len), target_start)
  }

  return len
}

// fill(value, start=0, end=buffer.length)
Buffer.prototype.fill = function (value, start, end) {
  if (!value) value = 0
  if (!start) start = 0
  if (!end) end = this.length

  if (end < start) throw new RangeError('end < start')

  // Fill 0 bytes; we're done
  if (end === start) return
  if (this.length === 0) return

  if (start < 0 || start >= this.length) throw new RangeError('start out of bounds')
  if (end < 0 || end > this.length) throw new RangeError('end out of bounds')

  var i
  if (typeof value === 'number') {
    for (i = start; i < end; i++) {
      this[i] = value
    }
  } else {
    var bytes = utf8ToBytes(value.toString())
    var len = bytes.length
    for (i = start; i < end; i++) {
      this[i] = bytes[i % len]
    }
  }

  return this
}

/**
 * Creates a new `ArrayBuffer` with the *copied* memory of the buffer instance.
 * Added in Node 0.12. Only available in browsers that support ArrayBuffer.
 */
Buffer.prototype.toArrayBuffer = function () {
  if (typeof Uint8Array !== 'undefined') {
    if (Buffer.TYPED_ARRAY_SUPPORT) {
      return (new Buffer(this)).buffer
    } else {
      var buf = new Uint8Array(this.length)
      for (var i = 0, len = buf.length; i < len; i += 1) {
        buf[i] = this[i]
      }
      return buf.buffer
    }
  } else {
    throw new TypeError('Buffer.toArrayBuffer not supported in this browser')
  }
}

// HELPER FUNCTIONS
// ================

var BP = Buffer.prototype

/**
 * Augment a Uint8Array *instance* (not the Uint8Array class!) with Buffer methods
 */
Buffer._augment = function (arr) {
  arr.constructor = Buffer
  arr._isBuffer = true

  // save reference to original Uint8Array get/set methods before overwriting
  arr._get = arr.get
  arr._set = arr.set

  // deprecated, will be removed in node 0.13+
  arr.get = BP.get
  arr.set = BP.set

  arr.write = BP.write
  arr.toString = BP.toString
  arr.toLocaleString = BP.toString
  arr.toJSON = BP.toJSON
  arr.equals = BP.equals
  arr.compare = BP.compare
  arr.copy = BP.copy
  arr.slice = BP.slice
  arr.readUIntLE = BP.readUIntLE
  arr.readUIntBE = BP.readUIntBE
  arr.readUInt8 = BP.readUInt8
  arr.readUInt16LE = BP.readUInt16LE
  arr.readUInt16BE = BP.readUInt16BE
  arr.readUInt32LE = BP.readUInt32LE
  arr.readUInt32BE = BP.readUInt32BE
  arr.readIntLE = BP.readIntLE
  arr.readIntBE = BP.readIntBE
  arr.readInt8 = BP.readInt8
  arr.readInt16LE = BP.readInt16LE
  arr.readInt16BE = BP.readInt16BE
  arr.readInt32LE = BP.readInt32LE
  arr.readInt32BE = BP.readInt32BE
  arr.readFloatLE = BP.readFloatLE
  arr.readFloatBE = BP.readFloatBE
  arr.readDoubleLE = BP.readDoubleLE
  arr.readDoubleBE = BP.readDoubleBE
  arr.writeUInt8 = BP.writeUInt8
  arr.writeUIntLE = BP.writeUIntLE
  arr.writeUIntBE = BP.writeUIntBE
  arr.writeUInt16LE = BP.writeUInt16LE
  arr.writeUInt16BE = BP.writeUInt16BE
  arr.writeUInt32LE = BP.writeUInt32LE
  arr.writeUInt32BE = BP.writeUInt32BE
  arr.writeIntLE = BP.writeIntLE
  arr.writeIntBE = BP.writeIntBE
  arr.writeInt8 = BP.writeInt8
  arr.writeInt16LE = BP.writeInt16LE
  arr.writeInt16BE = BP.writeInt16BE
  arr.writeInt32LE = BP.writeInt32LE
  arr.writeInt32BE = BP.writeInt32BE
  arr.writeFloatLE = BP.writeFloatLE
  arr.writeFloatBE = BP.writeFloatBE
  arr.writeDoubleLE = BP.writeDoubleLE
  arr.writeDoubleBE = BP.writeDoubleBE
  arr.fill = BP.fill
  arr.inspect = BP.inspect
  arr.toArrayBuffer = BP.toArrayBuffer

  return arr
}

var INVALID_BASE64_RE = /[^+\/0-9A-z\-]/g

function base64clean (str) {
  // Node strips out invalid characters like \n and \t from the string, base64-js does not
  str = stringtrim(str).replace(INVALID_BASE64_RE, '')
  // Node converts strings with length < 2 to ''
  if (str.length < 2) return ''
  // Node allows for non-padded base64 strings (missing trailing ===), base64-js does not
  while (str.length % 4 !== 0) {
    str = str + '='
  }
  return str
}

function stringtrim (str) {
  if (str.trim) return str.trim()
  return str.replace(/^\s+|\s+$/g, '')
}

function isArrayish (subject) {
  return isArray(subject) || Buffer.isBuffer(subject) ||
      subject && typeof subject === 'object' &&
      typeof subject.length === 'number'
}

function toHex (n) {
  if (n < 16) return '0' + n.toString(16)
  return n.toString(16)
}

function utf8ToBytes (string, units) {
  units = units || Infinity
  var codePoint
  var length = string.length
  var leadSurrogate = null
  var bytes = []
  var i = 0

  for (; i < length; i++) {
    codePoint = string.charCodeAt(i)

    // is surrogate component
    if (codePoint > 0xD7FF && codePoint < 0xE000) {
      // last char was a lead
      if (leadSurrogate) {
        // 2 leads in a row
        if (codePoint < 0xDC00) {
          if ((units -= 3) > -1) bytes.push(0xEF, 0xBF, 0xBD)
          leadSurrogate = codePoint
          continue
        } else {
          // valid surrogate pair
          codePoint = leadSurrogate - 0xD800 << 10 | codePoint - 0xDC00 | 0x10000
          leadSurrogate = null
        }
      } else {
        // no lead yet

        if (codePoint > 0xDBFF) {
          // unexpected trail
          if ((units -= 3) > -1) bytes.push(0xEF, 0xBF, 0xBD)
          continue
        } else if (i + 1 === length) {
          // unpaired lead
          if ((units -= 3) > -1) bytes.push(0xEF, 0xBF, 0xBD)
          continue
        } else {
          // valid lead
          leadSurrogate = codePoint
          continue
        }
      }
    } else if (leadSurrogate) {
      // valid bmp char, but last char was a lead
      if ((units -= 3) > -1) bytes.push(0xEF, 0xBF, 0xBD)
      leadSurrogate = null
    }

    // encode utf8
    if (codePoint < 0x80) {
      if ((units -= 1) < 0) break
      bytes.push(codePoint)
    } else if (codePoint < 0x800) {
      if ((units -= 2) < 0) break
      bytes.push(
        codePoint >> 0x6 | 0xC0,
        codePoint & 0x3F | 0x80
      )
    } else if (codePoint < 0x10000) {
      if ((units -= 3) < 0) break
      bytes.push(
        codePoint >> 0xC | 0xE0,
        codePoint >> 0x6 & 0x3F | 0x80,
        codePoint & 0x3F | 0x80
      )
    } else if (codePoint < 0x200000) {
      if ((units -= 4) < 0) break
      bytes.push(
        codePoint >> 0x12 | 0xF0,
        codePoint >> 0xC & 0x3F | 0x80,
        codePoint >> 0x6 & 0x3F | 0x80,
        codePoint & 0x3F | 0x80
      )
    } else {
      throw new Error('Invalid code point')
    }
  }

  return bytes
}

function asciiToBytes (str) {
  var byteArray = []
  for (var i = 0; i < str.length; i++) {
    // Node's code seems to be doing this and not & 0x7F..
    byteArray.push(str.charCodeAt(i) & 0xFF)
  }
  return byteArray
}

function utf16leToBytes (str, units) {
  var c, hi, lo
  var byteArray = []
  for (var i = 0; i < str.length; i++) {
    if ((units -= 2) < 0) break

    c = str.charCodeAt(i)
    hi = c >> 8
    lo = c % 256
    byteArray.push(lo)
    byteArray.push(hi)
  }

  return byteArray
}

function base64ToBytes (str) {
  return base64.toByteArray(base64clean(str))
}

function blitBuffer (src, dst, offset, length, unitSize) {
  if (unitSize) length -= length % unitSize
  for (var i = 0; i < length; i++) {
    if ((i + offset >= dst.length) || (i >= src.length))
      break
    dst[i + offset] = src[i]
  }
  return i
}

function decodeUtf8Char (str) {
  try {
    return decodeURIComponent(str)
  } catch (err) {
    return String.fromCharCode(0xFFFD) // UTF 8 invalid char
  }
}

},{"base64-js":3,"ieee754":4,"is-array":5}],3:[function(require,module,exports){
var lookup = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

;(function (exports) {
	'use strict';

  var Arr = (typeof Uint8Array !== 'undefined')
    ? Uint8Array
    : Array

	var PLUS   = '+'.charCodeAt(0)
	var SLASH  = '/'.charCodeAt(0)
	var NUMBER = '0'.charCodeAt(0)
	var LOWER  = 'a'.charCodeAt(0)
	var UPPER  = 'A'.charCodeAt(0)
	var PLUS_URL_SAFE = '-'.charCodeAt(0)
	var SLASH_URL_SAFE = '_'.charCodeAt(0)

	function decode (elt) {
		var code = elt.charCodeAt(0)
		if (code === PLUS ||
		    code === PLUS_URL_SAFE)
			return 62 // '+'
		if (code === SLASH ||
		    code === SLASH_URL_SAFE)
			return 63 // '/'
		if (code < NUMBER)
			return -1 //no match
		if (code < NUMBER + 10)
			return code - NUMBER + 26 + 26
		if (code < UPPER + 26)
			return code - UPPER
		if (code < LOWER + 26)
			return code - LOWER + 26
	}

	function b64ToByteArray (b64) {
		var i, j, l, tmp, placeHolders, arr

		if (b64.length % 4 > 0) {
			throw new Error('Invalid string. Length must be a multiple of 4')
		}

		// the number of equal signs (place holders)
		// if there are two placeholders, than the two characters before it
		// represent one byte
		// if there is only one, then the three characters before it represent 2 bytes
		// this is just a cheap hack to not do indexOf twice
		var len = b64.length
		placeHolders = '=' === b64.charAt(len - 2) ? 2 : '=' === b64.charAt(len - 1) ? 1 : 0

		// base64 is 4/3 + up to two characters of the original data
		arr = new Arr(b64.length * 3 / 4 - placeHolders)

		// if there are placeholders, only get up to the last complete 4 chars
		l = placeHolders > 0 ? b64.length - 4 : b64.length

		var L = 0

		function push (v) {
			arr[L++] = v
		}

		for (i = 0, j = 0; i < l; i += 4, j += 3) {
			tmp = (decode(b64.charAt(i)) << 18) | (decode(b64.charAt(i + 1)) << 12) | (decode(b64.charAt(i + 2)) << 6) | decode(b64.charAt(i + 3))
			push((tmp & 0xFF0000) >> 16)
			push((tmp & 0xFF00) >> 8)
			push(tmp & 0xFF)
		}

		if (placeHolders === 2) {
			tmp = (decode(b64.charAt(i)) << 2) | (decode(b64.charAt(i + 1)) >> 4)
			push(tmp & 0xFF)
		} else if (placeHolders === 1) {
			tmp = (decode(b64.charAt(i)) << 10) | (decode(b64.charAt(i + 1)) << 4) | (decode(b64.charAt(i + 2)) >> 2)
			push((tmp >> 8) & 0xFF)
			push(tmp & 0xFF)
		}

		return arr
	}

	function uint8ToBase64 (uint8) {
		var i,
			extraBytes = uint8.length % 3, // if we have 1 byte left, pad 2 bytes
			output = "",
			temp, length

		function encode (num) {
			return lookup.charAt(num)
		}

		function tripletToBase64 (num) {
			return encode(num >> 18 & 0x3F) + encode(num >> 12 & 0x3F) + encode(num >> 6 & 0x3F) + encode(num & 0x3F)
		}

		// go through the array every three bytes, we'll deal with trailing stuff later
		for (i = 0, length = uint8.length - extraBytes; i < length; i += 3) {
			temp = (uint8[i] << 16) + (uint8[i + 1] << 8) + (uint8[i + 2])
			output += tripletToBase64(temp)
		}

		// pad the end with zeros, but make sure to not forget the extra bytes
		switch (extraBytes) {
			case 1:
				temp = uint8[uint8.length - 1]
				output += encode(temp >> 2)
				output += encode((temp << 4) & 0x3F)
				output += '=='
				break
			case 2:
				temp = (uint8[uint8.length - 2] << 8) + (uint8[uint8.length - 1])
				output += encode(temp >> 10)
				output += encode((temp >> 4) & 0x3F)
				output += encode((temp << 2) & 0x3F)
				output += '='
				break
		}

		return output
	}

	exports.toByteArray = b64ToByteArray
	exports.fromByteArray = uint8ToBase64
}(typeof exports === 'undefined' ? (this.base64js = {}) : exports))

},{}],4:[function(require,module,exports){
exports.read = function(buffer, offset, isLE, mLen, nBytes) {
  var e, m,
      eLen = nBytes * 8 - mLen - 1,
      eMax = (1 << eLen) - 1,
      eBias = eMax >> 1,
      nBits = -7,
      i = isLE ? (nBytes - 1) : 0,
      d = isLE ? -1 : 1,
      s = buffer[offset + i];

  i += d;

  e = s & ((1 << (-nBits)) - 1);
  s >>= (-nBits);
  nBits += eLen;
  for (; nBits > 0; e = e * 256 + buffer[offset + i], i += d, nBits -= 8);

  m = e & ((1 << (-nBits)) - 1);
  e >>= (-nBits);
  nBits += mLen;
  for (; nBits > 0; m = m * 256 + buffer[offset + i], i += d, nBits -= 8);

  if (e === 0) {
    e = 1 - eBias;
  } else if (e === eMax) {
    return m ? NaN : ((s ? -1 : 1) * Infinity);
  } else {
    m = m + Math.pow(2, mLen);
    e = e - eBias;
  }
  return (s ? -1 : 1) * m * Math.pow(2, e - mLen);
};

exports.write = function(buffer, value, offset, isLE, mLen, nBytes) {
  var e, m, c,
      eLen = nBytes * 8 - mLen - 1,
      eMax = (1 << eLen) - 1,
      eBias = eMax >> 1,
      rt = (mLen === 23 ? Math.pow(2, -24) - Math.pow(2, -77) : 0),
      i = isLE ? 0 : (nBytes - 1),
      d = isLE ? 1 : -1,
      s = value < 0 || (value === 0 && 1 / value < 0) ? 1 : 0;

  value = Math.abs(value);

  if (isNaN(value) || value === Infinity) {
    m = isNaN(value) ? 1 : 0;
    e = eMax;
  } else {
    e = Math.floor(Math.log(value) / Math.LN2);
    if (value * (c = Math.pow(2, -e)) < 1) {
      e--;
      c *= 2;
    }
    if (e + eBias >= 1) {
      value += rt / c;
    } else {
      value += rt * Math.pow(2, 1 - eBias);
    }
    if (value * c >= 2) {
      e++;
      c /= 2;
    }

    if (e + eBias >= eMax) {
      m = 0;
      e = eMax;
    } else if (e + eBias >= 1) {
      m = (value * c - 1) * Math.pow(2, mLen);
      e = e + eBias;
    } else {
      m = value * Math.pow(2, eBias - 1) * Math.pow(2, mLen);
      e = 0;
    }
  }

  for (; mLen >= 8; buffer[offset + i] = m & 0xff, i += d, m /= 256, mLen -= 8);

  e = (e << mLen) | m;
  eLen += mLen;
  for (; eLen > 0; buffer[offset + i] = e & 0xff, i += d, e /= 256, eLen -= 8);

  buffer[offset + i - d] |= s * 128;
};

},{}],5:[function(require,module,exports){

/**
 * isArray
 */

var isArray = Array.isArray;

/**
 * toString
 */

var str = Object.prototype.toString;

/**
 * Whether or not the given `val`
 * is an array.
 *
 * example:
 *
 *        isArray([]);
 *        // > true
 *        isArray(arguments);
 *        // > false
 *        isArray('');
 *        // > false
 *
 * @param {mixed} val
 * @return {bool}
 */

module.exports = isArray || function (val) {
  return !! val && '[object Array]' == str.call(val);
};

},{}],6:[function(require,module,exports){
// shim for using process in browser

var process = module.exports = {};
var queue = [];
var draining = false;

function drainQueue() {
    if (draining) {
        return;
    }
    draining = true;
    var currentQueue;
    var len = queue.length;
    while(len) {
        currentQueue = queue;
        queue = [];
        var i = -1;
        while (++i < len) {
            currentQueue[i]();
        }
        len = queue.length;
    }
    draining = false;
}
process.nextTick = function (fun) {
    queue.push(fun);
    if (!draining) {
        setTimeout(drainQueue, 0);
    }
};

process.title = 'browser';
process.browser = true;
process.env = {};
process.argv = [];
process.version = ''; // empty string to avoid regexp issues

function noop() {}

process.on = noop;
process.addListener = noop;
process.once = noop;
process.off = noop;
process.removeListener = noop;
process.removeAllListeners = noop;
process.emit = noop;

process.binding = function (name) {
    throw new Error('process.binding is not supported');
};

// TODO(shtylman)
process.cwd = function () { return '/' };
process.chdir = function (dir) {
    throw new Error('process.chdir is not supported');
};
process.umask = function() { return 0; };

},{}],7:[function(require,module,exports){
//========================================================================================
// Globals
//========================================================================================

var Context = require("./context").Context;

var PRIMITIVE_TYPES = {
    'UInt8'    : 1,
    'UInt16LE' : 2,
    'UInt16BE' : 2,
    'UInt32LE' : 4,
    'UInt32BE' : 4,
    'Int8'     : 1,
    'Int16LE'  : 2,
    'Int16BE'  : 2,
    'Int32LE'  : 4,
    'Int32BE'  : 4,
    'FloatLE'  : 4,
    'FloatBE'  : 4,
    'DoubleLE' : 8,
    'DoubleBE' : 8
};

var SPECIAL_TYPES = {
    'String'   : null,
    'Buffer'   : null,
    'Array'    : null,
    'Skip'     : null,
    'Choice'   : null,
    'Nest'     : null,
    'Bit'      : null
};

var BIT_RANGE = [];
(function() {
    var i;
    for (i = 1; i <= 32; i++) {
        BIT_RANGE.push(i);
    }
})();

// Converts Parser's method names to internal type names
var NAME_MAP = {};
Object.keys(PRIMITIVE_TYPES)
    .concat(Object.keys(SPECIAL_TYPES))
    .forEach(function(type) {
        NAME_MAP[type.toLowerCase()] = type;
    });

//========================================================================================
// class Parser
//========================================================================================

//----------------------------------------------------------------------------------------
// constructor
//----------------------------------------------------------------------------------------

var Parser = function() {
    this.varName = '';
    this.type = '';
    this.options = {};
    this.next = null;
    this.head = null;
    this.compiled = null;
    this.endian = 'be';
    this.constructorFn = null;
};

//----------------------------------------------------------------------------------------
// public methods
//----------------------------------------------------------------------------------------

Parser.start = function() {
    return new Parser();
};

Object.keys(PRIMITIVE_TYPES)
    .forEach(function(type) {
        Parser.prototype[type.toLowerCase()] = function(varName, options) {
            return this.setNextParser(type.toLowerCase(), varName, options);
        };

        var typeWithoutEndian = type.replace(/BE|LE/, '').toLowerCase();
        if (!(typeWithoutEndian in Parser.prototype)) {
            Parser.prototype[typeWithoutEndian] = function(varName, options) {
                return this[typeWithoutEndian + this.endian](varName, options);
            };
        }
    });

BIT_RANGE.forEach(function(i) {
    Parser.prototype['bit' + i.toString()] = function(varName, options) {
        if (!options) {
            options = {};
        }
        options.length = i;
        return this.setNextParser('bit', varName, options);
    };
});

Parser.prototype.skip = function(length, options) {
    if (options && options.assert) {
        throw new Error('assert option on skip is not allowed.');
    }

    return this.setNextParser('skip', '', {length: length});
};

Parser.prototype.string = function(varName, options) {
    if (!options.zeroTerminated && !options.length) {
        throw new Error('Length option of string is not defined.');
    }
    options.encoding = options.encoding || 'utf8';

    return this.setNextParser('string', varName, options);
};

Parser.prototype.buffer = function(varName, options) {
    if (!options.length && !options.readUntil) {
        throw new Error('Length nor readUntil is defined in buffer parser');
    }

    return this.setNextParser('buffer', varName, options);
};

Parser.prototype.array = function(varName, options) {
    if (!options.readUntil && !options.length) {
        throw new Error('Length option of array is not defined.');
    }
    if (!options.type) {
        throw new Error('Type option of array is not defined.');
    }
    if (typeof options.type === 'string' && Object.keys(PRIMITIVE_TYPES).indexOf(NAME_MAP[options.type]) < 0) {
        throw new Error('Specified primitive type "' + options.type + '" is not supported.');
    }

    return this.setNextParser('array', varName, options);
};

Parser.prototype.choice = function(varName, options) {
    if (!options.tag) {
        throw new Error('Tag option of array is not defined.');
    }
    if (!options.choices) {
        throw new Error('Choices option of array is not defined.');
    }
    Object.keys(options.choices).forEach(function(key) {
        if (isNaN(parseInt(key, 10))) {
            throw new Error('Key of choices must be a number.');
        }
        if (!options.choices[key]) {
            throw new Error('Choice Case ' + key + ' of ' + varName + ' is not valid.');
        }

        if (typeof options.choices[key] === 'string' && Object.keys(PRIMITIVE_TYPES).indexOf(NAME_MAP[options.choices[key]]) < 0) {
            throw new Error('Specified primitive type "' +  options.choices[key] + '" is not supported.');
        }
    });

    return this.setNextParser('choice', varName, options);
};

Parser.prototype.nest = function(varName, options) {
    if (!options.type) {
        throw new Error('Type option of nest is not defined.');
    }
    if (!(options.type instanceof Parser)) {
        throw new Error('Type option of nest must be a Parser object.');
    }

    return this.setNextParser('nest', varName, options);
};

Parser.prototype.endianess = function(endianess) {
    switch (endianess.toLowerCase()) {
    case 'little':
        this.endian = 'le';
        break;
    case 'big':
        this.endian = 'be';
        break;
    default:
        throw new Error('Invalid endianess: ' + endianess);
    }

    return this;
};

Parser.prototype.create = function(constructorFn) {
    if (!(constructorFn instanceof Function)) {
        throw new Error('Constructor must be a Function object.');
    }

    this.constructorFn = constructorFn;

    return this;
};

Parser.prototype.getCode = function() {
    var ctx = new Context();

    if (this.constructorFn) {
        ctx.pushCode('var vars = new constructorFn();');
    } else {
        ctx.pushCode('var vars = {};');
    }
    ctx.pushCode('var offset = 0;');
    ctx.pushCode('if (!Buffer.isBuffer(buffer)) {');
    ctx.generateError('"argument buffer is not a Buffer object"');
    ctx.pushCode('}');

    this.generate(ctx);

    ctx.pushCode('return vars;');

    return ctx.code;
};

Parser.prototype.compile = function() {
    this.compiled = new Function('buffer', 'callback', 'constructorFn', this.getCode());
};

Parser.prototype.sizeOf = function() {
    var size = NaN;

    if (Object.keys(PRIMITIVE_TYPES).indexOf(this.type) >= 0) {
        size = PRIMITIVE_TYPES[this.type];

    // if this is a fixed length string
    } else if (this.type === 'String' && typeof this.options.length === 'number') {
        size = this.options.length;

    // if this is a fixed length array
    } else if (this.type === 'Array' && typeof this.options.length === 'number') {
        var elementSize = NaN;
        if (typeof this.options.type === 'string'){
            elementSize = PRIMITIVE_TYPES[NAME_MAP[this.options.type]];
        } else if (this.options.type instanceof Parser) {
            elementSize = this.options.type.sizeOf();
        }
        size = this.options.length * elementSize;

    // if this a skip
    } else if (this.type === 'Skip') {
        size = this.options.length;

    } else if (!this.type) {
        size = 0;
    }

    if (this.next) {
        size += this.next.sizeOf();
    }

    return size;
};

// Follow the parser chain till the root and start parsing from there
Parser.prototype.parse = function(buffer, callback) {
    if (!this.compiled) {
        this.compile();
    }

    return this.compiled(buffer, callback, this.constructorFn);
};

//----------------------------------------------------------------------------------------
// private methods
//----------------------------------------------------------------------------------------

Parser.prototype.setNextParser = function(type, varName, options) {
    var parser = new Parser();

    parser.type = NAME_MAP[type];
    parser.varName = varName;
    parser.options = options || parser.options;
    parser.endian = this.endian;

    if (this.head) {
        this.head.next = parser;
    } else {
        this.next = parser;
    }
    this.head = parser;

    return this;
};

// Call code generator for this parser
Parser.prototype.generate = function(ctx) {
    if (this.type) {
        this['generate' + this.type](ctx);
        this.generateAssert(ctx);
    }

    var varName = ctx.generateVariable(this.varName);
    if (this.options.formatter) {
        this.generateFormatter(ctx, varName, this.options.formatter);
    }

    return this.generateNext(ctx);
};

Parser.prototype.generateAssert = function(ctx) {
    if (!this.options.assert) {
        return;
    }

    var varName = ctx.generateVariable(this.varName);

    switch (typeof this.options.assert) {
        case 'function':
            ctx.pushCode('if (!({0}).call(vars, {1})) {', this.options.assert, varName);
        break;
        case 'number':
            ctx.pushCode('if ({0} !== {1}) {', this.options.assert, varName);
        break;
        case 'string':
            ctx.pushCode('if ("{0}" !== {1}) {', this.options.assert, varName);
        break;
        default:
            throw new Error('Assert option supports only strings, numbers and assert functions.');
    }
    ctx.generateError('"Assert error: {0} is " + {0}', varName);
    ctx.pushCode('}');
};

// Recursively call code generators and append results
Parser.prototype.generateNext = function(ctx) {
    if (this.next) {
        ctx = this.next.generate(ctx);
    }

    return ctx;
};

Object.keys(PRIMITIVE_TYPES).forEach(function(type) {
    Parser.prototype['generate' + type] = function(ctx) {
        ctx.pushCode('{0} = buffer.read{1}(offset);', ctx.generateVariable(this.varName), type);
        ctx.pushCode('offset += {0};', PRIMITIVE_TYPES[type]);
    };
});

Parser.prototype.generateBit = function(ctx) {
    // TODO find better method to handle nested bit fields
    var parser = JSON.parse(JSON.stringify(this));
    parser.varName = ctx.generateVariable(parser.varName);
    ctx.bitFields.push(parser);

    if (!this.next || (this.next && ['Bit', 'Nest'].indexOf(this.next.type) < 0)) {
        var sum = 0;
        ctx.bitFields.forEach(function(parser) {
            sum += parser.options.length;
        });

        var val = ctx.generateTmpVariable();

        if (sum <= 8) {
            ctx.pushCode('var {0} = buffer.readUInt8(offset);', val);
            sum = 8;
        } else if (sum <= 16) {
            ctx.pushCode('var {0} = buffer.readUInt16BE(offset);', val);
            sum = 16;
        } else if (sum <= 32) {
            ctx.pushCode('var {0} = buffer.readUInt32BE(offset);', val);
            sum = 32;
        } else {
            throw new Error('Currently, bit field sequence longer than 4-bytes is not supported.');
        }
        ctx.pushCode('offset += {0};', sum / 8);

        var bitOffset = 0;
        var isBigEndian = this.endian === 'be';
        ctx.bitFields.forEach(function(parser) {
            ctx.pushCode('{0} = {1} >> {2} & {3};',
                parser.varName,
                val,
                isBigEndian ? sum - bitOffset - parser.options.length : bitOffset,
                (1 << parser.options.length) - 1
            );
            bitOffset += parser.options.length;
        });

        ctx.bitFields = [];
    }
};

Parser.prototype.generateSkip = function(ctx) {
    var length = ctx.generateOption(this.options.length);
    ctx.pushCode('offset += {0};', length);
};

Parser.prototype.generateString = function(ctx) {
    if(this.options.length) {
        var name = ctx.generateVariable(this.varName);
        ctx.pushCode('{0} = buffer.toString(\'{1}\', offset, offset + {2});',
                            name,
                            this.options.encoding,
                            ctx.generateOption(this.options.length)
                        );
        if(this.options.stripNull)
        {
            ctx.pushCode('{0} = {0}.replace(/\0/g, \'\')', name);
        }
        ctx.pushCode('offset += {0};', ctx.generateOption(this.options.length));
    }
    else {
        var start = ctx.generateTmpVariable();

        ctx.pushCode('var {0} = offset;', start);
        ctx.pushCode('while(buffer.readUInt8(offset++) !== 0);');
        ctx.pushCode('{0} = buffer.toString(\'{1}\', {2}, offset - 1);',
            ctx.generateVariable(this.varName),
            this.options.encoding,
            start
        );
    }
};

Parser.prototype.generateBuffer = function(ctx) {
    if (this.options.readUntil === 'eof') {
        ctx.pushCode('{0} = buffer.slice(offset, buffer.length - 1);',
            ctx.generateVariable(this.varName)
            );
    } else {
        ctx.pushCode('{0} = buffer.slice(offset, offset + {1});',
            ctx.generateVariable(this.varName),
            ctx.generateOption(this.options.length)
            );
        ctx.pushCode('offset += {0};', ctx.generateOption(this.options.length));
    }

    if (this.options.clone) {
        var buf = ctx.generateTmpVariable();

        ctx.pushCode('var {0} = new Buffer({1}.length);', buf, ctx.generateVariable(this.varName));
        ctx.pushCode('{0}.copy({1});', ctx.generateVariable(this.varName), buf);
        ctx.pushCode('{0} = {1}', ctx.generateVariable(this.varName), buf);
    }
};

Parser.prototype.generateArray = function(ctx) {
    var length = ctx.generateOption(this.options.length);
    var type = this.options.type;
    var counter = ctx.generateTmpVariable();
    var lhs = ctx.generateVariable(this.varName);
    var item = ctx.generateTmpVariable();
    var key = this.options.key;
    var isHash = typeof key === 'string';

    if (isHash) {
        ctx.pushCode('{0} = {};', lhs);
    } else {
        ctx.pushCode('{0} = [];', lhs);
    }
    if (typeof this.options.readUntil === 'function') {
        ctx.pushCode('do {');
    } else if (this.options.readUntil === 'eof') {
        ctx.pushCode('for (var {0} = 0; offset < buffer.length; {0}++) {', counter);
    } else {
        ctx.pushCode('for (var {0} = 0; {0} < {1}; {0}++) {', counter, length);
    }

    if (typeof type === 'string') {
        ctx.pushCode('var {0} = buffer.read{1}(offset);', item, NAME_MAP[type]);
        ctx.pushCode('offset += {0};', PRIMITIVE_TYPES[NAME_MAP[type]]);
    } else if (type instanceof Parser) {
        ctx.pushCode('var {0} = {};', item);

        ctx.pushScope(item);
        type.generate(ctx);
        ctx.popScope();
    }

    if (isHash) {
        ctx.pushCode('{0}[{2}.{1}] = {2};', lhs, key, item);
    } else {
        ctx.pushCode('{0}.push({1});', lhs, item);
    }

    ctx.pushCode('}');

    if (typeof this.options.readUntil === 'function') {
        ctx.pushCode(' while (!({0}).call(this, {1}, buffer.slice(offset)));', this.options.readUntil, item);
    }
};

Parser.prototype.generateChoiceCase = function(ctx, varName, type) {
    if (typeof type === 'string') {
        ctx.pushCode('{0} = buffer.read{1}(offset);', ctx.generateVariable(this.varName), NAME_MAP[type]);
        ctx.pushCode('offset += {0};', PRIMITIVE_TYPES[NAME_MAP[type]]);
    } else if (type instanceof Parser) {
        ctx.pushPath(varName);
        type.generate(ctx);
        ctx.popPath();
    }
};

Parser.prototype.generateChoice = function(ctx) {
    var tag = ctx.generateOption(this.options.tag);

    ctx.pushCode('{0} = {};', ctx.generateVariable(this.varName));
    ctx.pushCode('switch({0}) {', tag);
    Object.keys(this.options.choices).forEach(function(tag) {
        var type = this.options.choices[tag];

        ctx.pushCode('case {0}:', tag);
        this.generateChoiceCase(ctx, this.varName, type);
        ctx.pushCode('break;');
    }, this);
    ctx.pushCode('default:');
    if (this.options.defaultChoice) {
        this.generateChoiceCase(ctx, this.varName, this.options.defaultChoice);
    } else {
        ctx.generateError('"Met undefined tag value " + {0} + " at choice"', tag);
    }
    ctx.pushCode('}');
};

Parser.prototype.generateNest = function(ctx) {
    var nestVar = ctx.generateVariable(this.varName);
    ctx.pushCode('{0} = {};', nestVar);
    ctx.pushPath(this.varName);
    this.options.type.generate(ctx);
    ctx.popPath();
};

Parser.prototype.generateFormatter = function(ctx, varName, formatter) {
    if (typeof formatter === 'function') {
        ctx.pushCode('{0} = ({1}).call(this, {0});', varName, formatter);
    }
}

Parser.prototype.isInteger = function() {
    return !!this.type.match(/U?Int[8|16|32][BE|LE]?|Bit\d+/);
};

//========================================================================================
// Exports
//========================================================================================

exports.Parser = Parser;

},{"./context":8}],8:[function(require,module,exports){
//========================================================================================
// class Context
//========================================================================================

//----------------------------------------------------------------------------------------
// constructor
//----------------------------------------------------------------------------------------

var Context = function() {
    this.code = '';
    this.scopes = [['vars']];
    this.isAsync = false;
    this.bitFields = [];
    this.tmpVariableCount = 0;
};

//----------------------------------------------------------------------------------------
// public methods
//----------------------------------------------------------------------------------------

Context.prototype.generateVariable = function(name) {
    var arr = [];

    Array.prototype.push.apply(arr, this.scopes[this.scopes.length - 1]);
    if (name) {
        arr.push(name);
    }

    return arr.join('.');
};

Context.prototype.generateOption = function(val) {
    switch(typeof val) {
        case 'number':
            return val.toString();
        case 'string':
            return this.generateVariable(val);
        case 'function':
            return '(' + val + ').call(' + this.generateVariable() + ')';
    }
};

Context.prototype.generateError = function() {
    var args = Array.prototype.slice.call(arguments);
    var err = Context.interpolate.apply(this, args);

    if (this.isAsync) {
        this.pushCode('return process.nextTick(function() { callback(new Error(' + err + '), vars); });');
    } else {
        this.pushCode('throw new Error(' + err + ');');
    }
};

Context.prototype.generateTmpVariable = function() {
    return '$tmp' + (this.tmpVariableCount++);
};

Context.prototype.pushCode = function() {
    var args = Array.prototype.slice.call(arguments);
 
    this.code += Context.interpolate.apply(this, args) + '\n';
};

Context.prototype.pushPath = function(name) {
    this.scopes[this.scopes.length - 1].push(name);
};

Context.prototype.popPath = function() {
    this.scopes[this.scopes.length - 1].pop();
};

Context.prototype.pushScope = function(name) {
    this.scopes.push([name]);
};

Context.prototype.popScope = function() {
    this.scopes.pop();
};

//----------------------------------------------------------------------------------------
// private methods
//----------------------------------------------------------------------------------------

Context.interpolate = function(s) {
    var re = /{\d+}/g;
    var matches = s.match(re);
    var params = Array.prototype.slice.call(arguments, 1);

    if (matches) {
        matches.forEach(function(match) {
            var index = parseInt(match.substr(1, match.length - 2), 10);
            s = s.replace(match, params[index].toString());
        });
    }

    return s;
};

exports.Context = Context;

},{}],9:[function(require,module,exports){
(function (Buffer){
"use strict";
//===----------------------------------------------------------------------===//
//
// NAME         : pe-html.js
// SUMMARY      : Parses the PE/COFF format and outputs to to HTML/
// COPYRIGHT    : (c) 2015 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
// DESCRIPTION  : Parse the Microsoft Portable Executable and Common Object File
//                Format which is most commonly used as the format of
//                executables on Microsoft Windows and renders the output to
//                HTML so it can be displayed in a web browser.
//
//===----------------------------------------------------------------------===//

var pe = require('./pe.js');

// Given the structure defintion (Parser()) object used to parse the field,
// associate the variable name with the value.
function formatWithNames(structure, fields, dest)
{
  for (var item = structure.next; item; item = item.next)
  {
    dest.innerHTML +=
      '<li class="item">' +
        '<strong class="name">' + item.varName + ':</strong>' +
        '<span class="value">'  +
           fields[item.varName].toLocaleString() +
            ' (0x' + fields[item.varName].toString(16) + ')' +
        '</span>' +
      '</li>';
  }
};

function writeBitmapToImageToScreen()
{
  var bitmapIndex = 0;
  var bitmapsDiv = document.getElementById('pe-bitmaps');
  bitmapsDiv.innerHTML = '';
  function writeFile(bitmapData)
  {
    var base64EncodedAsciiString = bitmapData.toString('base64')
    bitmapsDiv.innerHTML += '<img src="data:image/bmp;base64,' +
      base64EncodedAsciiString + '">';
  }
  return writeFile;
}

function fileProvided(file)
{
  var reader = new FileReader();
  reader.addEventListener("loadend", function(event) {
    // reader.result contains the contents of blob as a typed array
    var data = new Int8Array(event.target.result);
    var peData = pe.parseFile(data);

    var dest = document.getElementById('pe-results');
    formatWithNames(pe.structures.DosHeader, peData.dosHeader, dest);

    var peHeaderStructure = pe.structures.NtHeader.next.options.type;
    formatWithNames(peHeaderStructure, peData.ntHeader.Main, dest);

    var optionalHeaderStructure = pe.structures.NtHeader.next.next.options.type;
    formatWithNames(optionalHeaderStructure, peData.ntHeader.Optional, dest);

    // Import table.
    var importTableDiv = document.getElementById('pe-import-table');
    if (!peData.importTable || peData.importTable.length === 0)
    {
      importTableDiv.innerHTML = 'No information available';
    }
    else
    {
      importTableDiv.innerHTML = '';
      for (var i = 0; i < peData.importTable.length; ++i)
      {
        importTableDiv.innerHTML += '<h5>' + peData.importTable[i].Name +
          '</h5>';
        var newList = document.createElement("ul");
        formatWithNames(pe.structures.ImportDirectoryEntry,
                        peData.importTable[i],
                        newList);

        var nameList = document.createElement("ul");
        for (var j = 0; j < peData.importTable[i].Names.length; ++j)
        {
          var name = peData.importTable[i].Names[j];
          nameList.innerHTML += '<li class="item">' + name.Name + '</li>';
        }

        var title = document.createElement("strong");
        title.className = 'name';
        title.innerHTML = 'Names:';

        var li = document.createElement("li");
        li.className = 'item';
        li.appendChild(title);
        li.appendChild(nameList);

        newList.appendChild(li);

        importTableDiv.appendChild(newList);
      }
    }

    pe.forEachBitmap(peData, writeBitmapToImageToScreen(), true);
    var bitmapsDiv = document.getElementById('pe-bitmaps');
    if (bitmapsDiv.innerHTML.length === 0)
    {
      bitmapsDiv.innerHTML = 'No bitmaps could be found in the executable';
    }
  });

  // Start the read.
  reader.readAsArrayBuffer(file);
}

// Register the call-back for when a file is provided to the input field.
document.getElementById('file-field').addEventListener("change", function(event)
{
  if (event.target.files.length === 0)
  {
    var dest = document.getElementById('pe-results');
    dest.innerHTML = '';
    var importTableDiv = document.getElementById('pe-import-table');
    importTableDiv.innerHTML = 'No executable has been loaded so there is no ' +
                               'import table to show.';
    var bitmapsDiv = document.getElementById('pe-bitmaps');
    bitmapsDiv.innerHTML = 'No executable has been loaded so there is no ' +
                           'bitmaps to show.';
  }
  else if (event.target.files.length === 1)
  {
    fileProvided(event.target.files[0]);
  }
  else
  {
    alert('Support for multiple files at once has not been implemented');
  }
});

// Make Buffer a global as the binary-parser module generates code which expects
// Buffer to be in the global namespace.
window.Buffer = Buffer;

}).call(this,require("buffer").Buffer)
},{"./pe.js":10,"buffer":2}],10:[function(require,module,exports){
(function (process,Buffer){
"use strict";
//===----------------------------------------------------------------------===//
//
// NAME         : pe.js
// SUMMARY      : Parses the PE/COFF format commonly used for executables.
// COPYRIGHT    : (c) 2015 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
// DESCRIPTION  : Parse the Microsoft Portable Executable and Common Object File
//                Format which is most commonly used as the format of
//                executables on Microsoft Windows.
//
// At this stage it defines some of the structures used in the format which
// can be used to parse an executable.
//
// At the moment it will try to open an executable, find the bitmaps stored in
// the resource section and write out each bitmap to a file.
//
//===----------------------------------------------------------------------===//

var Parser = require('binary-parser').Parser;

var dosHeader = new Parser()
  .endianess('little')
  .uint16('magic', {assert: 0x5A4D})
  .uint16("LastSize")
  .uint16("BlockCount")
  .uint16("ReallocationCount")
  .uint16("HeaderSize")
  .uint16("MinAlloc")
  .uint16("MaxAlloc")
  .uint16("InitialRelativeSS")
  .uint16("InitialSP")
  .uint16("Checksum")
  .uint16("InitialIP")
  .uint16("InitialRelativeCS")
  .uint16("RelocationTableAddress")
  .uint16("OverlayCount")
  .array('Reserved1', {
    type: 'int16le',
    length: 4,
    })
  .int16("OemID")
  .int16("OemInfo")
  .array('Reserved2', {
    type: 'int16le',
    length: 10,
    })
  .uint32("NewExeHeaderAddress");

// https://msdn.microsoft.com/en-us/library/windows/desktop/ms680313.aspx
// plus signature from IMAGE_NT_HEADERS.
// https://msdn.microsoft.com/en-us/library/windows/desktop/ms680336.aspx.
var peHeader = new Parser()
  .endianess('little')
  .uint32('magic') // TODO: Add the assertion...
  .uint16('MachineType')
  .uint16("SectionCount")
  .uint32("DateTimeStamp")
  .uint32("SymbolTableFileOffset")
  .uint32("SymbolCount")
  .uint16("OptionalHeaderSize")
  .uint16("Characteristics");

function formatDataDirectories(directories)
{
  // Assigns a name to the directory such that it can be looked up by-name.
  //
  // Empty directories will be ignored where an empty directory is one with an
  // Address of zero and Size of zero.

  // The following list is from 2.4.3. Optional Header Data Directories and
  // it corresponds to the elements in peHeaderOptional.DataDirectories.
  var dataDirectoryIndexToName = [
    'ExportTable',
    'ImportTable',
    'ResourceTable',
    'ExceptionTable',
    'CertificateTable',
    'BaseRelocationTable',
    'Debug',
    'Architecture', // Reserved and unused.
    'GlobalPointer',
    'TLSTable', // Thread local storage table address.
    'LoadConfigurationTable',
    'BoundImportTable',
    'ImportAddressTable',
    'DelayImportDescriptor',
    'CLRRuntimeHeader'
    ];

  var byName = {};
  for (var i = 0; i < directories.length; ++i)
  {
    if (directories[i].Address === 0 && directories[i].Size === 0) continue;
    var index = dataDirectoryIndexToName[i] || i;
    byName[index] = directories[i];
  }
  return byName;
}

// https://msdn.microsoft.com/en-us/library/windows/desktop/ms680339.aspx
// This is section 2.4.1 Optional Header Standard Fields in the MPECOFF
// specification document.
var peHeaderOptional = new Parser()
  .endianess('little')
  .uint16("Magic", {assert: function(value) {
    return value === 0x010B || value === 0x020B; // PE32 or PE32+.
    }})
  .uint8("MajorLinkerVersion")
  .uint8("MinorLinkerVersion")
  .uint32("CodeSize")
  .uint32("InitializedDataSize")
  .uint32("UnitializedDataSize")
  .uint32("EntryPointAddress")
  .uint32("CodeBaseAddress")
  .choice('DataBaseAddress', {
    tag: 'Magic',
    choices: {
      0x010B: new Parser().uint32("DataBaseAddress"),
      0x020B: new Parser().skip(0)
    }})
  .choice('ImageBaseAddress', {
    tag: 'Magic',
    choices: {
      0x010B: new Parser().uint32("ImageBaseAddress"),
      0x020B: new Parser()
        // There is no 64-bit integer version. Buffer.readIntBE only supports
        // up to 48-bit integers.
        .uint32("ImageBaseAddressHigh")
        .uint32("ImageBaseAddressLow")
    }})
  .uint32("SectionAlignment")
  .uint32("FileAlignment")
  .uint16("MajorOperatingSystemVersion")
  .uint16("MinorOperatingSystemVersion")
  .uint16("MajorImageVersion")
  .uint16("MinorImageVersion")
  .uint16("MajorSubSystemVersion")
  .uint16("MinorSubSystemVersion")
  .uint32("Win32VersionValue", {assert: 0}) // This is reserved.
  .uint32("ImageSize")
  .uint32("HeadersSize")
  .uint32("CheckSum")
  .uint16("Subsystem")
  .uint16("DllCharacteristics")
  .uint32("StackReserveSize")
  .uint32("StackCommitSize")
  .uint32("HeapReserveSize")
  .uint32("HeapCommitSize")
  .uint32("LoadingFlag")
  .uint32("RvaAndSizesCount")
  .array('DataDirectories', {
    type: new Parser().endianess('little').uint32("Address").uint32("Size"),
    length: 'RvaAndSizesCount',
    formatter: formatDataDirectories
    });

// https://msdn.microsoft.com/en-us/library/windows/desktop/ms680336.aspx
var ntHeader = new Parser()
  .endianess('little')
  // Disclaimer: The MSDN version has hte magic part here where as instead,
  // I have put it into the peHeader which allows the peHeader to be easily
  // parsed without the optional header.
  .nest('Main', {type: peHeader})
  .nest('Optional', {type: peHeaderOptional});

// https://msdn.microsoft.com/en-us/library/windows/desktop/ms680341.aspx
var sectionHeader = new Parser()
  .endianess('little')
  .string("Name", {length: 8, stripNull: true})
  .uint32("VirtualSize")
  .uint32("VirtualAddress")
  .uint32("RawDataSize")
  .uint32("RawDataPointer")
  .uint32("RelocationPointer")
  .uint32("LineNumberPointer")
  .uint16("RelocationCount")
  .uint16("LineNumberCount")
  .uint32("Characteristics");

var resourceIDEntry = new Parser()
  .endianess('little')
  .uint32("ID")
  .uint32("Offset");

var resourceDirectoryTable = new Parser()
  .endianess('little')
  .uint32("Characteristics")
  .uint32("DateTimeStamp")
  .uint16("MajorVersion")
  .uint16("MinorVersion")
  .uint16("NameEntryCount")
  .uint16("IDEntryCount")
  .array('Entries', {
    length: function() { return this.IDEntryCount; },
    type: resourceIDEntry,
    });

var resourceDataEntry = new Parser()
  .endianess('little')
  .uint32("Offset")
  .uint32("Size")
  .uint32("CodePage")
  .uint32("Reserved");

// https://msdn.microsoft.com/en-us/library/windows/desktop/ms648009.aspx
var resourceIdType = {
  Cursor: 1,
  Bitmap: 2,
  Icon: 3,
  Menu: 4,
  DialogBox: 5,
  StringTableEntry: 6,
  FontDirectory: 7,
  Font: 8,
  AcceleratorTable: 9,
  RawData: 10,
  MessageTableEntry: 11,
  GroupCursor: 12,
  GroupIcon: 14,
  VersionInformation: 16,
  DlgInclude: 17,
  PlugAndPlay: 19,
  VXD: 20,
  AnimatedCursor: 21,
  AnimatedIcon: 22,
  HTML: 23,
  AssemblyManifest: 24,
  };

// Begin structures for parsing the .idata Section (also known as the import
// tables).
var importDirectoryEntry = new Parser()
  .endianess('little')
  .uint32("ImportNameTableAddress")
  .uint32("TimeDateStamp")
  .uint32("ForwarderChain")
  .uint32("NameAddress")
  .uint32("ImportAddressTableAddress");

var importDirectoryEntries = new Parser()
  .array('Entries', {
      type: importDirectoryEntry,
      readUntil: function (item, buf) {
        return item.ImportNameTableAddress === 0 &&
          item.TimeDateStamp === 0 &&
          item.ForwarderChain === 0 &&
          item.NameAddress === 0 &&
          item.ImportAddressTableAddress === 0;
        },
  });

var nameTableEntries = new Parser()
  .array('Names', {
    type: 'int32le',
    readUntil: function(item, buffer) { return item === 0 }
    })

var hintAndNameTableEntry = new Parser()
  .endianess('little')
  .uint16("Hint")
  .string("Name", {zeroTerminated: true});

// End of structures for parsing the .idata section.
function parseSectionHeaders(data, address, count)
{
  var sectionHeaders = new Parser()
    .endianess('little')
    .array('data', {
      type: sectionHeader,
      length: count,
    });

  return sectionHeaders.parse(data.slice(address)).data;
}

function utilFindIf(sequence, condition)
{
  for (var i = 0; i < sequence.length; ++i)
  {
    if (condition(sequence[i]))
    {
      return sequence[i];
    }
  }
  return null;
}

function parsePeFile(data)
{
  if (!Buffer.isBuffer(data)) {
    data = new Buffer(data);
  }

  var dosHeaderFromData = dosHeader.parse(data);
  var peHeaderFromData = peHeader.parse(
    data.slice(dosHeaderFromData.NewExeHeaderAddress));

  // This includes 'peHeaderFromData' and the optional header.
  var ntHeaderFromData = ntHeader.parse(
    data.slice(dosHeaderFromData.NewExeHeaderAddress));

  var sectionHeaderAddress = dosHeaderFromData.NewExeHeaderAddress +
    peHeaderFromData.OptionalHeaderSize + peHeader.sizeOf();

  var sectionHeadersFromData =
    parseSectionHeaders(data, sectionHeaderAddress, peHeaderFromData.SectionCount);

  var resourceSection = utilFindIf(sectionHeadersFromData,
    function(item) { return item.Name == '.rsrc'; });

  var bitmapDirectoryTableFromData;
  if (resourceSection)
  {
    var resourceDirectoryTableAddress = resourceSection.RawDataPointer;
    var resourceDirectoryTableFromData = resourceDirectoryTable.parse(
      data.slice(resourceDirectoryTableAddress));

    // Find the bitmap one.
    var bitmapEntry = utilFindIf(resourceDirectoryTableFromData.Entries,
      function(item) {
        return item.ID == resourceIdType.Bitmap; });

    // Read items in the bitmap entry.
    var entryA = resourceSection.RawDataPointer + (bitmapEntry.Offset & ~(1 << 31));
    bitmapDirectoryTableFromData = resourceDirectoryTable.parse(
      data.slice(entryA));
  }

  var directories = ntHeaderFromData.Optional.DataDirectories;
  // Read the import table if there is one.
  var importTable;
  if (directories && directories.ImportTable)
  {
    importTable =
      importDirectoryEntries.parse(data.slice(directories.ImportTable.Address));
    importTable = importTable.Entries;

    // Lets element the terminating element.
    importTable.pop();

    // TODO: Look into expanding the binary-parser library to make it possible
    // to say these bytes is an offset/address to type (primative or parser),
    // such that instead of 'NameAddress' it could simply be 'Name'.

    // Work around the above TODO by adding the Name to the table entries.
    var names = new Parser()
      .string('Name', {
        zeroTerminated : true
        });
    for (var i = 0; i < importTable.length; ++i)
    {
      var nameAddress = importTable[i].NameAddress;
      importTable[i].Name = names.parse(data.slice(nameAddress)).Name;

      // Parse the names.
      var address = importTable[i].ImportNameTableAddress;
      var nameEntries = nameTableEntries.parse(data.slice(address)).Names;
      var nameEntryValues = [];
      for (var j = 0; j < nameEntries.length; ++j)
      {
        var nameAddress = nameEntries[j];
        if (nameAddress === 0) continue;

        var name = hintAndNameTableEntry.parse(data.slice(nameAddress));
        nameEntryValues.push(name);
      }

      importTable[i].Names = nameEntryValues;
    }
  }

  return {
    'dosHeader': dosHeaderFromData,
    'ntHeader': ntHeaderFromData,
    'peHeader': peHeaderFromData,
    'sectionHeaders': sectionHeadersFromData,
    'resourceSection': resourceSection,
    'resourceDirectoryTable': resourceDirectoryTableFromData,
    'bitmapDirectoryTable': bitmapDirectoryTableFromData,
    'importTable': importTable,
    'rawData': data,
  }
}

function forEachBitmap(peData, callback, addHeader)
{
  // The bitmap header is 14 bytes:
  // 2-bytes for BM (0x42, 0x4D)
  // 4-bytes for file size.
  // 4-bytes padding.
  // 4-bytes for data offset

  if (!peData.bitmapDirectoryTable)
  {
    // There must not be any bitmaps in this image.
    return;
  }

  var bmpHeader = new Buffer([
    0x42, 0x4D, 0x76, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x76, 0x00,
    0x00, 0x00]);

  var bitmapDirectoryTableFromData = peData.bitmapDirectoryTable;
  var resourceSection = peData.resourceSection;
  for (var i = 0; i < bitmapDirectoryTableFromData.Entries.length; ++i)
  {
    var offset = bitmapDirectoryTableFromData.Entries[i].Offset;
    var entryB = resourceSection.RawDataPointer + (offset & ~(1 << 31));

    var nextTable = resourceDirectoryTable.parse(peData.rawData.slice(entryB))

    // The ID of this entry in the example I had was 1033 meaning its for
    // English.
    for (var j = 0; j < nextTable.Entries.length; ++j)
    {
      var offset = nextTable.Entries[j].Offset;
      var entryC = resourceSection.RawDataPointer + (offset & ~(1 << 31));
      var entry = resourceDataEntry.parse(peData.rawData.slice(entryC));

      // Now extract the bitmap data.
      var entryData = peData.rawData.slice(entry.Offset,
                                           entry.Offset + entry.Size);

      // Append the bitmap header.
      if (addHeader)
      {
        // Modify the bmpHeader to include the correct file size.
        var bmpSize = entryData.length + bmpHeader.length;
        bmpHeader[2] = (bmpSize & 0xFF);
        bmpHeader[3] = ((bmpSize >> 8) & 0xFF);

        entryData = Buffer.concat([bmpHeader, entryData]);
      }
      callback(entryData);
    }
  }
}

// Provides a callback function for use by the forEachBitmap function such that
// it will write out each bitmap to a separate file.
//
// This takes care of the addition of the bitmap header.
function writeBitmapToFile(fs)
{
  // TODO: The following BMP header is now universal, it won't work for all
  // bitmaps. It will work with the bitmaps in Ski32 (SkiFree) but not the
  // one in notepad.exe on WIndows 7.
  var bmpHeader = new Buffer([
    0x42, 0x4D, 0x76, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x76, 0x00,
    0x00, 0x00]);

  var bitmapIndex = 0;
  try
  {
    fs.mkdirSync('output');
  }
  catch (e) {}

  function writeFile(bitmapData)
  {
    var fd = fs.openSync('output/image_' + bitmapIndex.toString() + '.bmp',
                         'w');
    fs.write(fd, bmpHeader, 0, bmpHeader.length, 0, function(err,written){});
    fs.write(fd, bitmapData, 0, bitmapData.length, bmpHeader.length,
             function(err,written){});
    ++bitmapIndex;
  }
  return writeFile;
}

var main = function()
{
  var fs = require('fs');
  var data = fs.readFileSync(process.argv[2]);
  var peData = parsePeFile(data);
  console.log(peData.dosHeader);
  console.log(peData.ntHeader);
  console.log(peData.resourceDirectoryTable);

  console.log('Data directories: ');
  console.log(peData.ntHeader.Optional.DataDirectories);

  for (var i = 0; i < peData.importTable.length; ++i)
  {
    console.log(peData.importTable[i]);
  }

  forEachBitmap(peData, writeBitmapToFile(fs));
}

if (require.main === module) {
  main();
}

//========================================================================================
// Exports
//========================================================================================

exports.parseFile = parsePeFile;
exports.forEachBitmap = forEachBitmap ;
exports.structures = {
  'DosHeader': dosHeader,
  'NtHeader': ntHeader,
  'ResourceDirectoryTable': resourceDirectoryTable,
  'ResourceDataEntry': resourceDataEntry,
  'SectionHeader': sectionHeader,
  'ImportDirectoryEntry': importDirectoryEntry
  };

}).call(this,require('_process'),require("buffer").Buffer)
},{"_process":6,"binary-parser":7,"buffer":2,"fs":1}]},{},[9]);
