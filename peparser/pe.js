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
  .uint32("DataBaseAddress")
  .uint32("ImageBaseAddres")
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

  // Ideally there would be a way to say sizeof(peHeader);
  var sizeOfPeHeader = 24;

  var sectionHeaderAddress = dosHeaderFromData.NewExeHeaderAddress +
    peHeaderFromData.OptionalHeaderSize + sizeOfPeHeader;

  var sectionHeadersFromData =
    parseSectionHeaders(data, sectionHeaderAddress, peHeaderFromData.SectionCount);

  var resourceSection = utilFindIf(sectionHeadersFromData,
    function(item) { return item.Name == '.rsrc'; });

  var resourceDirectoryTableAddress = resourceSection.RawDataPointer;
  var resourceDirectoryTableFromData = resourceDirectoryTable.parse(
    data.slice(resourceDirectoryTableAddress));

  // FInd the bitmap one.
  var bitmapEntry = utilFindIf(resourceDirectoryTableFromData.Entries,
    function(item) {
      return item.ID == resourceIdType.Bitmap; });

  // Read items in the bitmap entry.
  var entryA = resourceSection.RawDataPointer + (bitmapEntry.Offset & ~(1 << 31));
  var bitmapDirectoryTableFromData = resourceDirectoryTable.parse(
    data.slice(entryA));

  var directories = ntHeaderFromData.Optional.DataDirectories;
  // Read the import table if there is one.
  var importTable;
  if (directories.ImportTable)
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
        var bmpSize = bitmapData.length + bmpHeader.length;
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

    // Modify the bmpHeader to include the correct file size.
    var bmpSize = bitmapData.length + bmpHeader.length;
    bmpHeader[2] = (bmpSize & 0xFF);
    bmpHeader[3] = ((bmpSize >> 8) & 0xFF);

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
