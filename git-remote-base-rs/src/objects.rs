// Provides tooling for working with git objects.
//
// Types of objects in git are: commit, tree, blob
//
// Loose objects are compressed with deflate from zlib.
//
// This only provides enough implementation needed for a git remote helper. It is not intended
// to provide complete handling of the object types.

pub enum ObjectType {
    Unknown,
    Commit, // Need to know the tree, and parents.
    Tree,
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

pub fn read_object_header(data: &String) -> ObjectHeader {
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

    let size = if let Some(size_ends) = data.find('\0') {
        let size_str = &data[size_start..size_ends];
        size_str.parse::<u32>().unwrap_or_else(|_| 0)
    } else {
        0
    };

    ObjectHeader {
        object_type: if is_commit {
            ObjectType::Commit {}
        } else if is_tree {
            ObjectType::Tree {}
        } else if is_blob {
            ObjectType::Blob {}
        } else {
            ObjectType::Unknown {}
        },
        size,
    }
}

#[cfg(test)]
mod tests {
    use crate::objects::{ObjectType, read_object_header};
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
        assert!(matches!(header.object_type, ObjectType::Commit));
        assert_eq!(header.size, 336);
        assert_eq!(string.len() - "commit 336\0".len(), 336);
    }

    // TODO: Add tree
    // TODO: Add blob
}
