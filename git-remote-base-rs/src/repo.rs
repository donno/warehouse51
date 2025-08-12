// Functions for working with a git repository on the local file system.
//
// The primary use is when cloning, this can be used to represent the repository where the
// clone is being made and more generally when fetching this helps manage the where the objects.

use std::io::{BufRead, Write};

pub struct Repository {
    path: std::path::PathBuf,
}

impl Repository {
    pub fn new(path: std::path::PathBuf) -> Self {
        Self { path }
    }

    // Return the path to where the pack files belong in the repository.
    pub fn pack_directory(&self) -> std::path::PathBuf {
        self.path.join("objects").join("pack")
    }

    // Return the path to where the object given by hash if it is a loose object is expected to be.
    //
    // Use `is_file()` to determine if the loose object exists.
    pub fn loose_object_path(&self, hash: &str) -> std::path::PathBuf {
        let object_directory = self.path.join("objects");
        object_directory.join(&hash[..2]).join(&hash[2..])
    }

    // Read the hash contained within a reference in the repository.
    pub fn read_reference(&self, reference: &str) -> Result<String, std::io::Error> {
        let file = std::fs::File::open(self.path.join(reference))?;
        let mut buffer = std::io::BufReader::new(file);
        let mut line = String::new();
        buffer.read_line(&mut line)?;
        Ok(line.trim_end().to_string())
    }

    // Write a reference to the repository.
    //
    // This or the caller needs a way to convert the reference into a remote reference, i.e.
    // "refs/heads/main" would be written to "refs/remotes/origin/main".
    //
    // contents will be either a commit ID or a reference to another reference.
    pub fn write_reference(&self, name: &str, contents: &str) -> Result<(), std::io::Error> {
        if !name.starts_with("refs/") {
            // Invalid reference.
            let reason = format!(
                "Unexpected name for a reference. Does not start with ref/. Value was: {}",
                name
            );
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                reason,
            ));
        }

        let reference_path = self.path.join(name);
        std::fs::create_dir_all(reference_path.parent().expect("Must have a parent"))?;

        let mut file = std::fs::File::create(reference_path.clone())?;
        file.write_all(contents.as_ref())?;
        Ok(())
    }
}
