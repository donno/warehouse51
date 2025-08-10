// Provides an implementation of the git-helper protocol using an existing repository.
//
// The implementation reads  and copies the appropriate files from an existing git repository on
// disk.
//
// In this case, I'm using the https://gist.github.com/donno/34aeb93dbaefa13a0d6a41953a17c024 as
// the demo.
// $ git clone base://fs/34aeb93dbaefa13a0d6a41953a17c024 34aeb93dbaefa13a0d6a41953a17c024_base
//
// The alternative is to use libgit2 to read the repository.

use crate::objects::{ObjectType, read_object_from_file};
use crate::protocol;
use log::{error, info, warn};
use std::collections::HashMap;
use std::io::BufRead;

pub struct FileBackedCommandHandler {
    remote_path: std::path::PathBuf,
    local_path: std::path::PathBuf,
    options: HashMap<String, String>,
}

impl FileBackedCommandHandler {
    pub fn new(url: url::Url, destination_path: std::path::PathBuf) -> Self {
        if url.path().is_empty() {
            panic!("Expected the URL to contain path: Use base://file/<repo-name>");
        }
        let base_path: std::path::PathBuf = match std::env::var_os("GIT_SOURCE_DIRECTORY") {
            Some(path) => path.into(),
            None => panic!("Environment variable GIT_SOURCE_DIRECTORY not set"),
        };

        info!("Outputting URL: {}", url);
        let source_path = base_path.join(&url.path()[1..]).join(".git");

        if !source_path.exists() {
            panic!(
                "The source repository could not be found at {}",
                source_path.display()
            );
        }

        FileBackedCommandHandler {
            remote_path: source_path,
            local_path: std::fs::canonicalize(destination_path)
                .expect("Can't canonicalise the destination path"),
            options: HashMap::new(),
        }
    }

    // For a fetch, this could be Option<> and so communicates if it exists or not.
    fn remote_loose_object_path(&self, hash: &str) -> std::path::PathBuf {
        let object_directory = self.remote_path.join("objects");
        object_directory.join(&hash[..2]).join(&hash[2..])
    }

    fn local_loose_object_path(&self, hash: &str) -> std::path::PathBuf {
        let destination_object_directory = self.local_path.join("objects");
        destination_object_directory
            .join(&hash[..2])
            .join(&hash[2..])
    }

    // Read the hash of a local reference.
    fn read_local_reference(&self, reference: &str) -> Result<String, std::io::Error> {
        let file = std::fs::File::open(self.local_path.join(reference))?;
        let mut buffer = std::io::BufReader::new(file);
        let mut line = String::new();
        buffer.read_line(&mut line)?;
        Ok(line.trim_end().to_string())
    }
    }
}

impl Default for FileBackedCommandHandler {
    fn default() -> Self {
        FileBackedCommandHandler {
            remote_path: match std::env::var_os("GIT_SOURCE_DIRECTORY") {
                Some(path) => path.into(),
                None => panic!("Environment variable GIT_SOURCE_DIRECTORY not set"),
            },
            local_path: match std::env::var_os("GIT_DIR") {
                Some(path) => path.into(),
                None => panic!("Environment variable $GIT_DIR not set"),
            },
            options: HashMap::new(),
        }
    }
}

fn read_lines<P>(filename: P) -> std::io::Result<std::io::Lines<std::io::BufReader<std::fs::File>>>
where
    P: AsRef<std::path::Path>,
{
    let file = std::fs::File::open(filename)?;
    Ok(std::io::BufReader::new(file).lines())
}

impl protocol::Command for FileBackedCommandHandler {
    fn set_option(&mut self, name: &str, value: &str) -> protocol::SetOptionResult {
        self.options.insert(name.to_string(), value.to_string());
        protocol::SetOptionResult::Ok {}
    }

    fn list_references(&self) -> Vec<protocol::Reference> {
        // Lists the refs, one per line, in the format "<value> <name> [<attr> ...]".
        //
        // Fake for now.
        // Mock version could use "git for-each-ref" on real one and strip out the type.
        let mut references = Vec::new();

        let refs_directory = self.remote_path.join("refs");

        let entries = std::fs::read_dir(refs_directory.clone()).unwrap();
        for entry in entries {
            match entry {
                Ok(entry) => {
                    if entry
                        .file_type()
                        .expect("Unable to determine file type.")
                        .is_dir()
                    {
                        let children = std::fs::read_dir(entry.path()).unwrap();
                        for child in children {
                            let child_entry = child.unwrap();
                            if child_entry.file_type().unwrap().is_file() {
                                let hash = if let Ok(mut lines) = read_lines(child_entry.path()) {
                                    lines.next().unwrap().unwrap()
                                } else {
                                    String::new()
                                };

                                if hash.is_empty() {
                                    continue;
                                }

                                match child_entry.path().strip_prefix(self.remote_path.clone()) {
                                    Ok(ref_name_path) => {
                                        let ref_name = ref_name_path
                                            .to_str()
                                            .expect("Expect UTF-8")
                                            .to_string();
                                        references.push(protocol::Reference {
                                            hash: hash.to_string(),
                                            // Slash conversion handles Windows style paths.
                                            name: ref_name.replace("\\", "/"),
                                        });
                                    }
                                    Err(_) => {
                                        error!("Failed to remove base-path prefix from path.")
                                    }
                                }
                            } else {
                                warn!(
                                    "Unhandled item in reference directory: {}",
                                    entry.path().display()
                                );
                            }
                        }
                    } else {
                        warn!(
                            "Unhandled file in reference directory: {}",
                            entry.path().display()
                        );
                    }
                }
                Err(_) => {
                    error!(
                        "Failed to read reference directory: {}",
                        refs_directory.display()
                    );
                }
            }
        }

        references
    }

    fn fetch_object(&self, hash: &str, name: &str) {
        // Fetch commands are sent in a batch, one per line, terminated with a blank line.
        // Outputs a single blank line when all fetch commands in the same batch are complete. Only objects which were reported in the output of list with a sha1 may be fetched this way.

        let mut objects_to_fetch = vec![hash.to_string()];
        while let Some(hash) = objects_to_fetch.pop() {
            let source_object = self.remote_loose_object_path(hash.as_str());
            if source_object.is_file() {
                // Found the object as a loose object.
                let destination_object = self.local_loose_object_path(hash.as_str());
                if destination_object.is_file() {
                    info!("Already fetched object: {}", hash);
                    continue;
                }
                info!(
                    "Fetching {} for '{}' - it was a loose object to {}",
                    hash,
                    name,
                    destination_object.display()
                );

                std::fs::create_dir_all(
                    destination_object
                        .parent()
                        .expect("Object path is sub-directory"),
                )
                .expect("TODO: Error handling");

                // Ideally, the file would be hashed first to make sure its content matches its
                // identity.
                std::fs::copy(source_object, destination_object.clone())
                    .expect("TODO: Error handling");

                let object = read_object_from_file(destination_object.clone())
                    .expect("TODO: Error handling for IO");
                match object {
                    ObjectType::Unknown => {
                        error!(
                            "Unrecognised type of object in the git object store: {}",
                            destination_object.display()
                        );
                    }
                    ObjectType::Commit { tree, parents } => {
                        // TODO: Not tested this yet.
                        // if let Some(tree) = tree
                        // {
                        //     objects_to_fetch.push(tree);
                        // }
                        for parent in parents {
                            objects_to_fetch.push(parent);
                        }
                    }
                    ObjectType::Tree => {
                        panic!("NYI - Fetching a tree");
                    }
                    ObjectType::Blob => {
                        // Nothing is required here as a blob if a leaf and doesn't reference any
                        // other objects.
                    }
                }

                // TODO: Need to handle fetching its dependencies.
            } else {
                // Didn't find the object, it may be in a pack file.
                info!(
                    "Fetching {} for '{}' - it was not a loose object - copying all packs.",
                    hash, name
                );

                // {self.remote_path}/.git/packed-refs has the hash associated with the given ref.
                //
                // To see what is within a given pack, check its index file:
                // $ git verify-pack -v .git/objects/pack/pack-<hash>.idx

                // To save doing that, if there is only one pack file, it can simply copy that.
                // Or quick and dirty copy all the packs for now.
                let remote_pack_directory = self.remote_path.join("objects").join("pack");
                let local_pack_directory = self.local_path.join("objects").join("pack");
                std::fs::create_dir_all(local_pack_directory.clone()).expect("Directory all good.");

                let entries = std::fs::read_dir(remote_pack_directory.clone()).unwrap();
                for entry in entries {
                    if let Ok(entry) = entry {
                        std::fs::copy(entry.path(), local_pack_directory.join(entry.file_name()))
                            .expect("TODO: Error handling");
                    }
                }
            }
        }
    }

    fn push(&self, source: &str, destination: &str, force_update: bool) {
        // The first step is to find what source refers to.
        //
        // This step could be good one to move into the caller of push() i.e. the protocol module as
        // reading the local repository will be common.
        if let Ok(local_reference) = self.read_local_reference(source) {
            if force_update {
                todo!(
                    "TODO: Handle force pushing {} ({}) to {}.",
                    source,
                    local_reference,
                    destination
                );
            } else {
                todo!(
                    "TODO: Handle pushing {} ({}) to {}.",
                    source,
                    local_reference,
                    destination
                );
            }

        // The way git-remote-s3 faked this was it would simply call "git bundle create" and upload
        // the entire thing, which is fine if you snapshotting.
        } else {
            eprintln!("Failed to read reference: {}", source);
        }
    }
}
