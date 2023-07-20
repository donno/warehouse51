// Very early days  getting up to compatible with peparser3.py.
//
use pelite::pe32::exports::Export;
use pelite::pe64::imports::Import;
use pelite::pe64::{Pe, PeFile};
use pelite::{FileMap, Result};
use std::path::Path;

// Start of with format similar to "dumpbin /imports"
fn print_imports(file: PeFile<'_>) -> pelite::Result<()> {
    let imports = file.imports()?;

    println!("Imports");
    println!("=======");

    for desc in imports {
        // DLL being imported from
        let dll_name = desc.dll_name()?;

        println!("{}", dll_name);

        // Import Address Table and Import Name Table for this imported DLL
        let iat = desc.iat()?;
        let int = desc.int()?;

        // For the  dumpbin /imports f

        let image = desc.image();

        // These two addresses are missing an offset as they have been
        // pre-processed by the library.
        println!(
            "{address:>16X} Import Address Table",
            address = image.FirstThunk
        );
        println!(
            "{address:>16X} Import Name Table",
            address = image.OriginalFirstThunk
        );
        println!(
            "{timestamp:>16} time date stamp",
            timestamp = image.TimeDateStamp
        );
        println!(
            "{timestamp:>16} index of first forwarder reference\n",
            timestamp = image.ForwarderChain
        );

        // Iterate over the imported functions from this DLL
        for (va, import) in Iterator::zip(iat, int) {
            if let Ok(import) = import {
                match import {
                    Import::ByName { hint, name } => {
                        println!("{hint:>16X} {name}", hint = hint, name = name);
                    }
                    Import::ByOrdinal { ord } => {
                        println!("                Ordinal {ordinal:>5}", ordinal = ord);
                    }
                }
            }
        }
        println!();
    }
    Ok(())
}

fn print_exports(file: PeFile<'_>) -> pelite::Result<()> {
    let exports = file.exports()?;

    // Print the export DLL name
    let dll_name = exports.dll_name()?;
    println!("dll_name: {}", dll_name);

    // Maybe zip of the names and functions. instead.
    let by = exports.by()?;
    // for result in by.iter() {
    //     println!("{}", result);
    // 	if let Ok(export) = result {
    // 		println!("export: {:?}", export);
    // 	}
    // }

    // For dumpbin format it should be:
    //     ordinal hint RVA      name
    for result in by.iter_names() {
        if let (Ok(name), Ok(export)) = result {
            match export {
                Export::Symbol(rva) => {
                    println!(
                        "<ordinal> <hint> {export:08X} {name}",
                        name = name,
                        export = rva
                    );
                }
                Export::Forward(fwd) => {
                    println!("forward {forward} {name}", name = name, forward = fwd);
                }
            }
        }
    }
    Ok(())
}

fn file_map<P: AsRef<Path> + ?Sized>(path: &P) -> Result<()> {
    let path = path.as_ref();
    if let Ok(map) = FileMap::open(path) {
        let file = PeFile::from_bytes(&map)?;

        // Access the file contents through the Pe trait
        let image_base = file.optional_header().ImageBase;
        println!(
            "The preferred load address of {:?} is {}.",
            path, image_base
        );

        // See the respective modules to access other parts of the PE file.

        //print_imports(file);
        print_exports(file);
    }
    Ok(())
}

fn main() {
    file_map("c:/Windows/System32/gdi32.dll").expect("Failed");
}
