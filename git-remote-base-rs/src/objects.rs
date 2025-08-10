// Provides tooling for working with git objects.
//
// Types of objects in git are: commit, tree, blob
//
// Loose objects are compressed with deflate from zlib.
//
// This only provides enough implementation needed for a git remote helper. It is not intended
// to provide complete handling of the object types.

use flate2::read::ZlibDecoder;
use std::io::Read;

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
    pub size: u32,
}

pub fn read_object_from_file(path: std::path::PathBuf) -> Result<ObjectType, std::io::Error> {
    let file = std::fs::File::open(path)?;
    let mut decoder = ZlibDecoder::new(file);

    // It would be nice to be above to ask for first 1024 decompressed bytes.
    let mut data = String::new();
    decoder.read_to_string(&mut data)?;
    Ok(read_object_header(&data).object_type)
}

pub fn read_object(decompressed_data: &String) -> ObjectType {
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

fn read_object_header(data: &String) -> ObjectHeader {
    // Alternative is to look at first char, then read the rest to confirm.
    const TYPE_PREFIX_COMMIT: &'static str = "commit ";
    const TYPE_PREFIX_TREE: &'static str = "tree ";
    const TYPE_PREFIX_BLOB: &'static str = "blob ";

    let is_commit = data.starts_with(TYPE_PREFIX_COMMIT);
    let is_tree = data.starts_with(TYPE_PREFIX_TREE);
    let is_blob = data.starts_with(TYPE_PREFIX_BLOB);

    // Between space and null is the size in ASCII.
    if !is_commit && !is_tree && !is_blob {
        return ObjectHeader {
            object_type: ObjectType::Unknown,
            size: 0,
        };
    }

    // The start is known based on the object type, so a find(' ') is not needed.
    let size_start = if is_commit {
        TYPE_PREFIX_COMMIT.len()
    } else if is_tree {
        TYPE_PREFIX_TREE.len()
    } else if is_blob {
        TYPE_PREFIX_BLOB.len()
    } else {
        0 // This should be unreachable as the statement above will exit in this case.
    };

    let size = if let Some(size_end) = data.find('\0') {
        let size_str = &data[size_start..size_end];
        size_str.parse::<u32>().unwrap_or_else(|_| 0)
    } else {
        0
    };

    // If no null character is found treat it as no data.
    let data_start = data.find('\0').unwrap_or(data.len() - 1) + 1;
    if is_commit {
        let mut lines = data[data_start..].lines();
        let tree = read_tree(lines.next());
        let parents = read_parents(lines);

        // read_parents() would have already read the next line, so it ideally should return
        // parents and next_line, however, this project doesn't need it.

        ObjectHeader {
            object_type: ObjectType::Commit { tree, parents },
            size,
        }
    } else if is_tree {
        ObjectHeader {
            object_type: ObjectType::Tree {},
            size,
        }
    } else if is_blob {
        ObjectHeader {
            object_type: ObjectType::Blob {},
            size,
        }
    } else {
        ObjectHeader {
            object_type: ObjectType::Unknown,
            size: 0,
        }
    }
}

#[cfg(test)]
mod tests {
    use crate::objects::{ObjectType, read_object_from_file, read_object_header};
    use flate2::read::ZlibDecoder;
    use std::io::Read;

    #[test]
    fn decode_commit() {
        let file = std::fs::File::open("testdata/e86ea53b653d62bfb5332a04877c563237ea69")
            .expect("Test data file should exist");
        let mut decoder = ZlibDecoder::new(file);

        // It would be nice to be above to ask for first 1024 decompressed bytes.
        let mut string = String::new();
        decoder.read_to_string(&mut string).unwrap();

        let header = read_object_header(&string);
        assert!(matches!(
            header.object_type,
            ObjectType::Commit {
                tree: _,
                parents: _
            }
        ));
        assert_eq!(header.size, 336);
        assert_eq!(string.len() - "commit 336\0".len(), 336);

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
    #[ignore] // Test doesn't pass yet due to stream not containing valid UTF-8.
    fn decode_tree_from_path() {
        let path = std::path::Path::new("testdata/e7691a046ef7d6dfc4bbf3862fff92f3641dd5");
        let object =
            read_object_from_file(path.to_path_buf()).expect("Test data should be readable.");
        assert!(matches!(object, ObjectType::Tree {},));

        // TODO: Test for the trees and blobs the tree references, once that is added.
    }

    // This project does not need to be able to read blobs.
}
