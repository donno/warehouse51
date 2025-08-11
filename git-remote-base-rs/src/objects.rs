// Provides tooling for working with git objects.
//
// Types of objects in git are: commit, tree, blob
//
// Loose objects are compressed with deflate from zlib.
//
// This only provides enough implementation needed for a git remote helper. It is not intended
// to provide complete handling of the object types.

use flate2::read::ZlibDecoder;
use memchr::memchr;
use std::io::{BufRead, Read};

const FIELD_PREFIX_TREE: &'static str = "tree ";
const FIELD_PREFIX_PARENT: &'static str = "parent ";

pub enum ObjectType {
    Unknown,
    Commit {
        tree: Option<String>,
        parents: Vec<String>,
        // The author, committer and commit message isn't required for this project.
    },
    Tree, // For tree, need to know other tree and blobs it references.
    Blob,
}

pub struct ObjectHeader {
    // The type of the object.
    //
    // This is based on the string at the start of the object.
    pub object_type: ObjectType,

    // The size of the object in bytes.
    pub size: usize,
}

pub fn read_object_from_file(path: std::path::PathBuf) -> Result<ObjectType, std::io::Error> {
    let file = std::fs::File::open(path)?;
    let mut decoder = ZlibDecoder::new(file);

    // It would be nice to be above to ask for first 1024 decompressed bytes.
    let mut buffer = Vec::new();
    decoder.read_to_end(&mut buffer)?;
    Ok(read_object_header(&buffer).object_type)
}

pub fn read_object(decompressed_data: &[u8]) -> ObjectType {
    read_object_header(decompressed_data).object_type
}

fn read_prefixed_line(line: Option<&str>, expected_prefix: &str) -> Option<String> {
    if let Some(line) = line {
        if line.starts_with(expected_prefix) {
            Some(line[expected_prefix.len()..].to_string())
        } else {
            None
        }
    } else {
        // Line was missing.
        None
    }
}

// Read the tree from an optional line.
fn read_tree(line: Option<&str>) -> Option<String> {
    return read_prefixed_line(line, FIELD_PREFIX_TREE);
}

fn read_parents(mut lines: std::str::Lines) -> Vec<String> {
    let mut parents = Vec::new();
    loop {
        let line = lines.next();
        if let Some(parent) = read_prefixed_line(line, FIELD_PREFIX_PARENT) {
            parents.push(parent);
        } else {
            break;
        }
    }
    parents
}

fn read_object_header(data: &[u8]) -> ObjectHeader {
    // The header starts with: <type>[space]<size>[NUL]
    let type_terminator = if let Some(type_terminator) = memchr(b' ', &data) {
        type_terminator + 1 // Include the space at the end.
    } else {
        // There was no space at all - invalid header.
        return ObjectHeader {
            object_type: ObjectType::Unknown,
            size: 0,
        };
    };

    let size_terminator = memchr(b'\0', &data);
    let size = if let Some(size_end) = size_terminator {
        let size_str = std::str::from_utf8(&data[type_terminator..size_end]).expect("not UTF-8");
        size_str.parse::<usize>().unwrap_or_else(|_| 0)
    } else {
        0
    };

    // If no null character is found treat it as no data.
    match &data[..type_terminator] {
        b"commit " => {
            let string =
                std::str::from_utf8(&data[size_terminator.unwrap() + 1..size]).expect("not UTF-8");
            let mut lines = string.lines();
            let tree = read_tree(lines.next());
            let parents = read_parents(lines);
            // read_parents() would have already read the next line, so it ideally should return
            // parents and next_line, however, this project doesn't need it.
            ObjectHeader {
                object_type: ObjectType::Commit { tree, parents },
                size,
            }
        }
        b"tree " => {
            // A tree object is made up of entries.
            // [mode] [entry-name]\0[SHA-1 of referencing blob or tree]
            //
            // TODO: Parse the above.
            ObjectHeader {
                object_type: ObjectType::Tree {},
                size,
            }
        }
        b"blob " => ObjectHeader {
            object_type: ObjectType::Blob {},
            size,
        },
        _ => ObjectHeader {
            object_type: ObjectType::Unknown,
            size: 0,
        },
    }
}

#[cfg(test)]
mod tests {
    use crate::objects::{
        FIELD_PREFIX_TREE, ObjectType, read_object_from_file, read_object_header,
    };
    use flate2::read::ZlibDecoder;
    use memchr::memchr;
    use std::io::{BufRead, Read};

    #[test]
    fn decode_commit() {
        let file = std::fs::File::open("testdata/e86ea53b653d62bfb5332a04877c563237ea69")
            .expect("Test data file should exist");
        let mut decoder = ZlibDecoder::new(file);

        // It would be nice to be above to ask for first 1024 decompressed bytes.
        let mut buffer = Vec::new();
        decoder
            .read_to_end(&mut buffer)
            .expect("Test data should be readable.");

        let header = read_object_header(&buffer);
        assert!(matches!(
            header.object_type,
            ObjectType::Commit {
                tree: _,
                parents: _
            }
        ));
        assert_eq!(header.size, 336);
        assert_eq!(buffer.len() - "commit 336\0".len(), 336);

        let expected_tree = "d4e7691a046ef7d6dfc4bbf3862fff92f3641dd5".to_string();
        let expected_parent = "69c3f5e740fd83a1e5d08f05055b3c4c1c98040d".to_string();
        if let ObjectType::Commit { tree, parents } = header.object_type.try_into().unwrap() {
            assert_eq!(tree, Some(expected_tree));
            assert_eq!(parents, vec!(expected_parent));
        }
    }

    #[test]
    fn decode_commit_from_path() {
        let path = std::path::Path::new("testdata/e86ea53b653d62bfb5332a04877c563237ea69");
        let object =
            read_object_from_file(path.to_path_buf()).expect("Test data should be readable.");
        assert!(matches!(
            object,
            ObjectType::Commit {
                tree: _,
                parents: _
            }
        ));

        let expected_tree = "d4e7691a046ef7d6dfc4bbf3862fff92f3641dd5".to_string();
        let expected_parent = "69c3f5e740fd83a1e5d08f05055b3c4c1c98040d".to_string();
        if let ObjectType::Commit { tree, parents } = object.try_into().unwrap() {
            assert_eq!(tree, Some(expected_tree));
            assert_eq!(parents, vec!(expected_parent));
        }
    }

    #[test]
    fn decode_tree() {
        let path = std::path::Path::new("testdata/e7691a046ef7d6dfc4bbf3862fff92f3641dd5");
        let file = std::fs::File::open(path).expect("Test data should exist.");
        let mut decoder = ZlibDecoder::new(file);
        let mut buffer = Vec::new();
        decoder
            .read_to_end(&mut buffer)
            .expect("Test data should be readable.");

        assert!(buffer.starts_with(b"tree "));

        let size_terminator = memchr(b'\0', &buffer).expect("Found terminator");
        let size_str = std::str::from_utf8(&buffer[5..size_terminator]).expect("not UTF-8");
        let size = size_str.parse::<usize>().unwrap_or_else(|_| 0);

        assert_eq!(size, 43);
    }

    #[test]
    fn decode_tree_from_path() {
        let path = std::path::Path::new("testdata/e7691a046ef7d6dfc4bbf3862fff92f3641dd5");
        let object =
            read_object_from_file(path.to_path_buf()).expect("Test data should be readable.");
        assert!(matches!(object, ObjectType::Tree {},));

        // TODO: Test for the trees and blobs the tree references, once that is added.
    }

    // This project does not need to be able to read blobs.
}
