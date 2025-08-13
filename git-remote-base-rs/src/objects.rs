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
    Tree {
        // The references can be other trees or blobs.
        references: Vec<String>,
        // The name and mode of the entries are required for this project so aren't collected.
    },
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

// Return a list of the references to other objects given by the object at the given path.
pub fn collect_references_from_loose_object(
    path: std::path::PathBuf,
) -> std::io::Result<Vec<String>> {
    let mut found_references = Vec::new();
    let object = read_object_from_file(path.clone())?;
    match object {
        ObjectType::Unknown => {
            let reason = format!(
                "Unrecognised type of object in the git object store: {}",
                path.display()
            );
            return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, reason));
        }
        ObjectType::Commit { tree, parents } => {
            if let Some(tree) = tree {
                found_references.push(tree);
            }
            for parent in parents {
                found_references.push(parent);
            }
        }
        ObjectType::Tree { references } => {
            found_references.extend(references);
        }
        ObjectType::Blob => {
            // Nothing is required here as a blob if a leaf and doesn't reference any
            // other objects.
        }
    }
    Ok(found_references)
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

struct TreeEntry {
    mode: String,
    name: String,
    hash: String,

    size: usize,
    // The size of the entry in the tree object.
}

// Read a tree entry in the form: [mode] [entry-name]\0[SHA-1 of referencing blob or tree]
fn read_tree_entry(data: &[u8]) -> Result<TreeEntry, String> {
    let first_separator = memchr(b' ', data);
    let second_separator = memchr(b'\0', data);
    if first_separator.is_none() {
        return Err("Invalid tree entry - no space found.".to_string());
    }
    if second_separator.is_none() {
        return Err("Invalid tree entry - no null terminator found after name.".to_string());
    }

    let name_end = second_separator.unwrap(); // Checked above.

    let mode = std::str::from_utf8(&data[..first_separator.unwrap()]).expect("not UTF-8");
    let name =
        std::str::from_utf8(&data[first_separator.unwrap() + 1..name_end]).expect("not UTF-8");
    const HASH_SIZE: usize = 20;

    Ok(TreeEntry {
        mode: mode.to_string(),
        name: name.to_string(),
        hash: hex::encode(&data[name_end + 1..name_end + 1 + HASH_SIZE]),
        size: name_end + 1 + HASH_SIZE,
    })
}

// Read the tree from an optional line.
fn read_tree(line: Option<&str>) -> Option<String> {
    read_prefixed_line(line, FIELD_PREFIX_TREE)
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
            // TODO: Keep reading entries until there are none-left.
            let data_start = size_terminator.unwrap() + 1;
            let data_end = data_start + size;

            let mut references = Vec::new();

            let mut entry_start = data_start;
            while entry_start < data_end {
                let entry = read_tree_entry(&data[entry_start..data_end]).expect("Entry");
                references.push(entry.hash);
                entry_start += entry.size + 1;
            }

            ObjectHeader {
                object_type: ObjectType::Tree { references },
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
    use crate::objects::{ObjectType, read_object_from_file, read_object_header, read_tree_entry};
    use flate2::read::ZlibDecoder;
    use memchr::memchr;
    use std::io::Read;

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

        // $ git cat-file -p d4e7691a046ef7d6dfc4bbf3862fff92f3641dd5
        // 100644 blob 45115f4b2a86b84dc323cbba9e53017f57dc8dc1    fetch_vcdist.py
        let entry = read_tree_entry(&buffer[size_terminator + 1..]).expect("Entry");
        assert_eq!(entry.name, "fetch_vcdist.py");
        assert_eq!(entry.mode, "100644");
        assert_eq!(entry.hash, "45115f4b2a86b84dc323cbba9e53017f57dc8dc1");
    }

    #[test]
    fn decode_tree_multiple_entries() {
        let path = std::path::Path::new("testdata/cdeea9ab369e5a1dd6f586e5464d13976a6263");
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

        assert_eq!(size, 393);

        // $ git cat-file -p 3acdeea9ab369e5a1dd6f586e5464d13976a6263
        // 100644 blob c472b4ea0a781061dab1f394627222735d4215bd    404.html
        // 100644 blob 12f97a480985b12fa2c6654d601ce260ce63b38a    _config.yml
        // 040000 tree 697458dce5850b4e134b11d940d49ac124f74b37    _drafts
        // Plus more.
        let entry = read_tree_entry(&buffer[size_terminator + 1..]).expect("Entry");
        assert_eq!(entry.name, "404.html");
        assert_eq!(entry.mode, "100644");
        assert_eq!(entry.hash, "c472b4ea0a781061dab1f394627222735d4215bd");

        // Problem with read_tree_entry() is it doesn't include the size of the entry so you
        // know where the next one is.
        //
        // The following calculates the offset based on the size of the previous entry.
        let second_entry =
            read_tree_entry(&buffer[9 + "100644".len() + 21 + size_terminator + 1..])
                .expect("Entry");
        assert_eq!(second_entry.name, "_config.yml");
        assert_eq!(second_entry.mode, "100644");
        assert_eq!(
            second_entry.hash,
            "12f97a480985b12fa2c6654d601ce260ce63b38a"
        );
    }

    #[test]
    fn decode_tree_from_path() {
        let path = std::path::Path::new("testdata/e7691a046ef7d6dfc4bbf3862fff92f3641dd5");
        let object =
            read_object_from_file(path.to_path_buf()).expect("Test data should be readable.");
        assert!(matches!(object, ObjectType::Tree { references: _ },));

        // TODO: Test for the trees and blobs the tree references, once that is added.
        let expected_blob = "45115f4b2a86b84dc323cbba9e53017f57dc8dc1".to_string();
        if let ObjectType::Tree { references } = object.try_into().unwrap() {
            assert_eq!(references, vec!(expected_blob));
        }
    }

    #[test]
    fn decode_tree_multiple_entries_from_path() {
        let path = std::path::Path::new("testdata/cdeea9ab369e5a1dd6f586e5464d13976a6263");
        let object =
            read_object_from_file(path.to_path_buf()).expect("Test data should be readable.");
        assert!(matches!(object, ObjectType::Tree { references: _ },));

        let expected_references = vec![
            "c472b4ea0a781061dab1f394627222735d4215bd".to_string(),
            "12f97a480985b12fa2c6654d601ce260ce63b38a".to_string(),
            "697458dce5850b4e134b11d940d49ac124f74b37".to_string(),
            "610986f34246d351aa1ff8a0481f30ee6db14971".to_string(),
            "14e993c397283385b2db77c2626ecf3660f1d9ea".to_string(),
            "e2e4392673a78eca0e2b39a6d63a83064b09689b".to_string(),
            "e64f70132181aba02f2e657c5787ffb32536a3d1".to_string(),
            "8cd655b97ace9c117ae2090411a797b15cf68294".to_string(),
            "2603ca6a57793ef890b81eee3f02b1f1eb93d0f6".to_string(),
            "e1791c9c70132438dd51fe2f0db45f88f01e24ca".to_string(),
            "7cad4a33f9b2a6cf06b9d99aec9f636d4011b54a".to_string(),
        ];

        if let ObjectType::Tree { references } = object.try_into().unwrap() {
            assert_eq!(references.len(), expected_references.len());
            assert_eq!(references, expected_references);
        }
    }

    // This project does not need to be able to read blobs.
}
