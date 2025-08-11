// The remote helper program (this program) is invoked with:
// one or optionally two arguments.
//
// - first argument specifies a remote repository as in Git
//   (either name of configured remote or URL)
// - second argument is the URL
//
// The GIT_DIR environment variable is set up for the remote
// helper and can be used to determine where to store additional data.
//
// See https://git-scm.com/docs/gitremote-helpers

use std::collections::HashMap;

use log::{LevelFilter, error, info, warn};

mod file;
mod objects;
mod protocol;

struct BaseCommandHandler {
    options: HashMap<String, String>,
}

impl Default for BaseCommandHandler {
    fn default() -> Self {
        BaseCommandHandler {
            options: HashMap::new(),
        }
    }
}

impl protocol::Command for BaseCommandHandler {
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
        references.push(protocol::Reference {
            hash: "5c3d2a42d88f8e13a1f50be0c46357b8f7760860".to_string(),
            name: "refs/heads/master".to_string(),
        });
        references
    }

    fn fetch_object(&self, hash: &str, name: &str) {
        // Fetch commands are sent in a batch, one per line, terminated with a blank line.
        // Outputs a single blank line when all fetch commands in the same batch are complete. Only objects which were reported in the output of list with a sha1 may be fetched this way.
        info!("Fetching {} for '{}'.", hash, name);
        todo!("Can't return the object yet.");
    }

    fn push(&self, source: &str, destination: &str, force_update: bool) {
        if force_update {
            todo!("TODO: Handle force pushing {} to {}.", source, destination);
        } else {
            todo!("TODO: Handle pushing {} to {}.", source, destination);
        }

        // Basic idea is this needs to resolve the source reference as the starting point.

        // The way git-remote-s3 faked this was it would simply call "git bundle create" and upload
        // the entire thing, which is fine if you snapshotting.
    }
}

// This was for another part of the protocol which would need to be opt-in.
// fn connect(service: &str) {
//     info!("Connecting to service '{}'", service);
// }

fn main() {
    // usage: git remote-base <remote> [<url>]
    //
    // However this is typically invoked via git clone base://
    //
    // As such git-remote-base was not best name, maybe "gitrs" would have
    // been better.
    let _ = simplelog::WriteLogger::init(
        LevelFilter::Info,
        simplelog::Config::default(),
        std::fs::File::create("remote-base-rs.log").unwrap(),
    );
    info!("Running remote helper");
    let mut args = std::env::args();
    let arguments = match protocol::parse_arguments(&mut args) {
        Ok(args) => args,
        Err(error) => panic!("{}", error),
    };

    let path: std::path::PathBuf = match std::env::var_os("GIT_DIR") {
        Some(path) => path.into(),
        None => panic!("Environment variable $GIT_DIR not set"),
    };

    info!("Name of program: {}", arguments.program);
    info!("Name of remote: {}", arguments.remote);
    info!("URL for remote: {}", arguments.url);
    info!("Git directory: {}", path.display());
    if arguments.url.scheme() != "base" {
        panic!("Expected the scheme of the URL to be \"base\".");
    }

    let mut handler = file::FileBackedCommandHandler::new(arguments.url, path);
    //let mut handler = BaseCommandHandler::default();
    loop {
        let mut input = String::new();
        match std::io::stdin().read_line(&mut input) {
            Ok(_) => {
                if !protocol::handle_command(input.to_string().trim(), &mut handler) {
                    break;
                }
            }
            Err(error) => {
                error!("Error reading next line of input: {}", error);
                println!("error: {error}")
            }
        }
    }

    //
}
