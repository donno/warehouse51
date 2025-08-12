// Provides an implementation of the git-helper protocol using an existing repository.
//
// The implementation reads and copies the appropriate files from an existing git repository on
// disk.
//
// In this case, I'm using the https://gist.github.com/donno/34aeb93dbaefa13a0d6a41953a17c024 as
// the demo.
// $ git clone base://fs/34aeb93dbaefa13a0d6a41953a17c024 34aeb93dbaefa13a0d6a41953a17c024_base
//
// The alternative is to use libgit2 to read the repository.

use crate::objects::collect_references_from_loose_object;
use crate::{protocol, repo};
use log::{error, info, warn};
use std::collections::HashMap;
use std::io::{BufRead, Error, Write};

pub struct FileBackedCommandHandler {
    remote_path: std::path::PathBuf,
    local: repo::Repository,
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
            local: repo::Repository::new(destination_path),
            options: HashMap::new(),
        }
    }

    // For a fetch, this could be Option<> and so communicates if it exists or not.
    fn remote_loose_object_path(&self, hash: &str) -> std::path::PathBuf {
        let object_directory = self.remote_path.join("objects");
        object_directory.join(&hash[..2]).join(&hash[2..])
    }

    // Write the hash of a remote reference.
    //
    // This is a case where using libgit2 would give better peace of mind.
    fn write_remote_reference(&self, reference: &str, hash: &str) -> Result<(), std::io::Error> {
        let mut file = std::fs::File::create(self.remote_path.join(reference))?;
        file.write_all(hash.as_ref())
    }

    fn remote_has_loose_object(&self, hash: &str) -> bool {
        let path = self.remote_loose_object_path(hash);
        path.is_file()
    }
}

impl Default for FileBackedCommandHandler {
    fn default() -> Self {
        let local_path: std::path::PathBuf = match std::env::var_os("GIT_DIR") {
            Some(path) => path.into(),
            None => panic!("Environment variable $GIT_DIR not set"),
        };

        FileBackedCommandHandler {
            remote_path: match std::env::var_os("GIT_SOURCE_DIRECTORY") {
                Some(path) => path.into(),
                None => panic!("Environment variable GIT_SOURCE_DIRECTORY not set"),
            },
            local: repo::Repository::new(local_path),
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
                let destination_object = self.local.loose_object_path(hash.as_str());
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

                // Find the dependencies of this given object and fetch them.
                match collect_references_from_loose_object(destination_object.clone()) {
                    Ok(references) => objects_to_fetch.extend(references),
                    Err(error) => todo!("Handle the error case: {}", error),
                }
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
                let local_pack_directory = self.local.pack_directory();
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

        // When cloning, the references for branches don't need to be written by the remote-helper.
        //
        // By default, all branches retrieved via the "list" command will be fetched and converted
        // to their remote equivalent by git itself.
    }

    fn push(&self, source: &str, destination: &str, force_update: bool) {
        // The first step is to find what source refers to.
        //
        // This step could be good one to move into the caller of push() i.e. the protocol module as
        // reading the local repository will be common.
        if let Ok(hash) = self.local.read_reference(source) {
            // The simple case is if the referenced object already exists upstream, in which case
            // the reference file simply needs to be written.
            //
            // If force_update is true, then it simply overwrites it if its already there
            // otherwise - it is involved.

            if force_update {
                todo!("TODO: Handle force pushing.");
            }

            // Handle pushing additional objects that are not on the remote.
            let mut objects_to_push = vec![hash.to_string()];
            let mut already_checked_objects = std::collections::HashSet::new();

            while let Some(hash) = objects_to_push.pop() {
                if already_checked_objects.contains(&hash.clone())
                    || self.remote_has_loose_object(hash.as_str())
                {
                    // Assume if the remote has the object then it has all the ancestors.
                    //
                    // In practice since this pushes the first object it comes across first this
                    // won't be true if the push is cancelled.
                    already_checked_objects.insert(hash);
                    continue;
                }

                let source_object = self.local.loose_object_path(hash.as_str());
                if source_object.is_file() {
                    info!(
                        "Pushing {} for '{}' - it was a loose object ({})",
                        hash,
                        destination,
                        source_object.display(),
                    );

                    let destination_object = self.remote_loose_object_path(hash.as_str());
                    std::fs::create_dir_all(
                        destination_object
                            .parent()
                            .expect("Object path is sub-directory"),
                    )
                    .expect("TODO: Error handling");

                    std::fs::copy(source_object.clone(), destination_object)
                        .expect("TODO: Error handling");

                    match collect_references_from_loose_object(source_object.clone()) {
                        Ok(references) => objects_to_push.extend(references),
                        Err(error) => todo!("Handle the error case: {}", error),
                    }
                } else {
                    // Similar to the fetch, simply copy all pack files to the remote.
                    info!(
                        "Pushing {} for '{}' - it was in a pack - all packs will be pushed",
                        hash, destination,
                    );

                    // Quick and dirty copy all the packs for now.
                    let remote_pack_directory = self.remote_path.join("objects").join("pack");
                    std::fs::create_dir_all(remote_pack_directory.clone())
                        .expect("Directory all good.");
                    let entries = std::fs::read_dir(self.local.pack_directory()).unwrap();
                    for entry in entries {
                        if let Ok(entry) = entry {
                            std::fs::copy(
                                entry.path(),
                                remote_pack_directory.join(entry.file_name()),
                            )
                            .expect("TODO: Error handling");
                        }
                    }
                }
            }

            info!("Writing reference '{}' with value {}", destination, hash);
            self.write_remote_reference(destination, hash.as_str())
                .expect("TODO: Handle IO errors");

            // The way git-remote-s3 faked this was it would simply call "git bundle create" and
            // upload the entire thing, which is fine if you snapshotting.
        } else {
            eprintln!("Failed to read reference: {}", source);
        }
    }

    fn finalisation(&self, remote_name: String) {
        // Write the refs/remotes/<name>/HEAD file if cloning.
        let false_string = "false".to_string();
        let cloning = self.options.get("cloning").unwrap_or(&false_string);
        if cloning == "true" {
            // TODO: This branch name won't work if it contains main.
            //
            // Revisit writing branches when fetching / cloning as the problem is it creates
            // local branches instead of ones in refs/remotes/<remote_name>.
            let contents = format!("ref: refs/remotes/{}/master", remote_name);
            match self.local.write_reference(
                format!("refs/remotes/{}/HEAD", remote_name).as_str(),
                contents.as_str(),
            ) {
                Ok(_) => {
                    info!("Wrote HEAD reference with value {}", contents);
                }
                Err(error) => {
                    error!("Unable to write HEAD reference: {}", error);
                }
            }
        }
    }
}
