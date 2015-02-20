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

  console.log(dosHeaderFromData);
  console.log(peHeaderFromData);

  // Ideally there would be a way to say sizeof(peHeader);
  var sizeOfPeHeader = 24;

  var sectionHeaderAddress = dosHeaderFromData.NewExeHeaderAddress +
    peHeaderFromData.OptionalHeaderSize + sizeOfPeHeader;

  var sectionHeadersFromData =
    parseSectionHeaders(data, sectionHeaderAddress, peHeaderFromData.SectionCount);

  var resourceSection = utilFindIf(sectionHeadersFromData,
    function(item) { return item.Name == '.rsrc'; });

  var resourceDirectoryTableAddress = resourceSection.RawDataPointer;
  console.log(resourceSection);
  var resourceDirectoryTableFromData = resourceDirectoryTable.parse(
    data.slice(resourceDirectoryTableAddress));

  console.log(resourceDirectoryTableFromData);

  // FInd the bitmap one.
  var bitmapEntry = utilFindIf(resourceDirectoryTableFromData.Entries,
    function(item) {
      return item.ID == resourceIdType.Bitmap; });

  console.log(bitmapEntry);

  // Read items in the bitmap entry.
  var entryA = resourceSection.RawDataPointer + (bitmapEntry.Offset & ~(1 << 31));
  var bitmapDirectoryTableFromData = resourceDirectoryTable.parse(
    data.slice(entryA));

  return {
    'dosHeader': dosHeaderFromData,
    'peHeader': peHeaderFromData,
    'sectionHeaders': sectionHeadersFromData,
    'resourceSection': resourceSection,
    'bitmapDirectoryTable': bitmapDirectoryTableFromData,
    'rawData': data,
  }
}

function forEachBitmap(peData, callback, addHeader)
{
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
function writeBitmapToFile()
{
  var bmpHeader = new Buffer([
    0x42, 0x4D, 0x76, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x76, 0x00,
    0x00, 0x00]);

  var bitmapIndex = 0;

  function writeFile(bitmapData)
  {
    var fd = fs.openSync('image_' + bitmapIndex.toString() + '.bmp', 'w');
    fs.write(fd, bmpHeader, 0, bmpHeader.length, 0, function(err,written){});
    fs.write(fd, bitmapData, 0, bitmapData.length, bmpHeader.length,
             function(err,written){});
    ++bitmapIndex;
  }
  return writeFile;
}

var fs = require('fs');
var data = fs.readFileSync(process.argv[2]);
var peData = parsePeFile(data);
forEachBitmap(peData, writeBitmapToFile());
