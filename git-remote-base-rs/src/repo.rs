// Functions for working with a git repository on the local file system.
//
// The primary use is when cloning, this can be used to represent the repository where the
// clone is being made and more generally when fetching this helps manage the where the objects.

use crate::objects::collect_references_from_loose_object;
use log::info;
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

    // Write a loose object into the object database based on an existing loose object on disk.
    //
    // Returns true if the object was written otherwise false if it already exists so no write was
    // required.
    pub fn write_loose_object_if_missing(
        &self,
        hash: &str,
        source_object: std::path::PathBuf,
    ) -> Result<bool, std::io::Error> {
        let destination_object = self.loose_object_path(hash);
        if destination_object.is_file() {
            return Ok(false);
        }

        std::fs::create_dir_all(
            destination_object
                .parent()
                .expect("Object path is sub-directory"),
        )?;

        // Ideally, the file would be hashed first to make sure its content matches its
        // identity.
        match std::fs::copy(source_object, destination_object.clone()) {
            Ok(_) => Ok(true),
            Err(error) => Err(error),
        }
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

pub enum FilesToPush {
    LooseObject {
        hash: String,
        path: std::path::PathBuf,
    },
    //Pack { index_path: std::path::PathBuf, pack_path: std::path::PathBuf},
    PackFile {
        path: std::path::PathBuf,
    },
}

pub trait HasObject {
    // Return true if the repository has object with the given hash.
    fn has_object(&self, hash: &str) -> bool;

    // Return true if the repository has pack file with the given name.
    fn has_pack_file(&self, name: &str) -> bool;
}

//type CheckHash = fn(&str) -> bool;

// Find loose objects to push to a remote which are missing them.
//
// This finds loose objects and packs to push to a remote based on if an object is missing in the
// remote.
pub fn find_objects_to_push(
    source: &Repository,
    start_hash: &str,
    remote: &impl HasObject,
) -> Vec<FilesToPush> {
    let mut objects_missing = Vec::new();

    let mut objects_to_push = vec![start_hash.to_string()];
    let mut already_checked_objects = std::collections::HashSet::new();

    let mut missing_packs = false;

    while let Some(hash) = objects_to_push.pop() {
        if already_checked_objects.contains(&hash.clone()) || remote.has_object(hash.as_str()) {
            // Assume if the remote has the object then it has all the ancestors.
            //
            // In practice since this pushes the first object it comes across first this
            // won't be true if the push is cancelled.
            already_checked_objects.insert(hash);
            continue;
        }

        let source_object = source.loose_object_path(hash.as_str());
        if source_object.is_file() {
            info!(
                "Remote is missing loose object {} at ({})",
                hash,
                source_object.display()
            );

            objects_missing.push(FilesToPush::LooseObject {
                hash,
                path: source_object.clone(),
            });

            match collect_references_from_loose_object(source_object.clone()) {
                Ok(references) => objects_to_push.extend(references),
                Err(error) => todo!("Handle the error case: {}", error),
            }
        } else {
            // Missing object - ideally this would find what pack the given object is in.
            // Similar to the fetch, simply copy all pack files to the remote.
            info!(
                "Remote is missing object that isn't loose ({}) - all packs will be pushed",
                hash
            );
            missing_packs = true;
        }
    }

    if missing_packs {
        // Quick and dirty copy all the packs for now.
        let entries = std::fs::read_dir(source.pack_directory()).unwrap();
        for entry in entries {
            if let Ok(entry) = entry {
                if ! remote.has_pack_file(&entry.file_name().into_string().expect("UTF-8"))
                {
                    objects_missing.push(FilesToPush::PackFile { path: entry.path() });
                }
            }
        }
    }

    objects_missing
}
