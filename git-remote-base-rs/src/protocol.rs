// This module helps provide the input format for remote helper programs.
//
// See https://git-scm.com/docs/gitremote-helpers
//
// Git sends the remote helper a list of commands on standard input, one per
// line.
//
//
// The sample conversation is:
// -> capabilities
// <- return list of capabilities
// -> option progress true (provided option is available).
// <- <empty line>
// -> option verbosity true (provided option is available).
// <- <empty line>
//
// list -> fetch -> ...

use log::{error, info};
use std::io::Write;

pub enum SetOptionResult {
    Ok,
    Unsupported,
    Error { message: String },
}

pub struct Arguments {
    pub program: String,
    pub remote: String,
    pub url: url::Url,
}

pub struct Reference {
    pub hash: String,
    pub name: String,
}

pub trait Command {
    // Sets the transport helper option <name> to <value>.
    fn set_option(&mut self, name: &str, value: &str) -> SetOptionResult;

    // Lists the references.
    //
    // The output is one per line, in the format "<value> <name> [<attr> ...]".
    fn list_references(&self) -> Vec<Reference>;

    // Fetches the given object, writing the necessary objects to the database.
    // TODO: expand this to include the path to the database.
    fn fetch_object(&self, hash: &str, name: &str);

    // Pushes the given local <src> commit or branch to the remote branch described by <dst>.
    //
    // Discover remote refs and push local commits and the history leading up to them to new or
    // existing remote refs.
    fn push(&self, source: &str, destination: &str, force_update: bool);

    // Perform any steps to finalise the operation.
    fn finalisation(&self, remote_name: String);
}

// Parse the arguments for a git-remote helper program.
pub fn parse_arguments(args: &mut std::env::Args) -> Result<Arguments, String> {
    let program = match args.next() {
        Some(program) => program,
        None => return Err("error: no arguments provided.".to_string()),
    };
    let remote = match args.next() {
        Some(remote) => remote,
        None => {
            return Err(format!(
                "error: {}: usage: git remote-base <remote> [<url>]",
                program,
            ));
        }
    };

    // TODO: If url was empty, then remote contains the url instead.
    let raw_url = match args.next() {
        Some(url) => url,
        // This is technically optional if it is not provided then remote is the url.
        None => {
            return Err(format!(
                "error: {}: expected <url> command line argument however it should be optional.",
                program
            ));
        }
    };

    let url = match url::Url::parse(raw_url.as_str()) {
        Ok(url) => url,
        Err(error) => return Err(format!("{:?}", error)),
    };

    Ok(Arguments {
        program,
        remote,
        url,
    })
}

fn handle_capabilities() {
    // TODO: This should be based on what the program supports.
    // Currently it is a hard-coded list while things are developed out.
    //    println!("connect");
    // The alternative is stateless-connect.
    // That uses git's wire-protocol version 2.

    println!("fetch");
    // "list" must be supported if the helper has the "fetch" or "import"
    // capability, and it does not need to be announced.

    println!("get");
    println!("option");

    println!("push");
    // "push" means the following commands are supported: list for-push, push.

    println!("check-connectivity");
    println!("object-format"); // This means "option object-format" should work.
    println!();
}

// Enum of the Capabilities might be good or if Command could dictate
// the capabilities. Or maybe an enum with the callbacks for optional parts.
pub fn handle_command(line: &str, handler: &mut impl Command) -> bool {
    let mut command_components = line.split(' ');
    let command: &str = command_components.next().unwrap_or_else(|| "");

    if command.is_empty() {
        // Assume it is the new-line terminating a batch of "fetch".
        info!("Received blank line - better handling of batch fetch NYI.");

        // Tell the caller we are done handling it.
        match writeln!(std::io::stdout(), "") {
            Ok(_) => info!("Successfully told caller that we are done."),
            Err(e) if e.kind() == std::io::ErrorKind::BrokenPipe => {
                error!("stdout is closed or broken.");
                return false;
            }
            Err(e) => error!("An unexpected error occurred: {}", e),
        }
        return true;
    }
    info!("Command received: {}", command);
    match command {
        "capabilities" => handle_capabilities(),
        "option" => {
            let name = match command_components.next() {
                Some(name) => name,
                None => {
                    error!("Option command requires a name. No name given.");
                    panic!("error: option expects a name.");
                }
            };
            let value = match command_components.next() {
                Some(value) => value,
                None => {
                    if name == "object-format" {
                        // This seems to support an implicit value.
                        "true"
                    } else {
                        error!(
                            "Option command requires a value for '{}'. No value given.",
                            name
                        );
                        panic!("error: option expects a value.");
                    }
                }
            };

            info!("Setting option '{}' to '{}'", name, value);
            let result = handler.set_option(name, value);

            // Outputs single line containing:
            // ok - option successfully set
            // unsupported (option not recognized)
            // error <msg> (option <name> is supported but <value> is not valid for it).
            match result {
                SetOptionResult::Ok => println!("ok"),
                SetOptionResult::Unsupported => println!("unsupported"),
                SetOptionResult::Error { message } => println!("error {}", message),
            }
        }
        // This option has been disabled.
        // "connect" => {
        //     // connect <service>
        //     let service = match command_components.next() {
        //         Some(service) => service,
        //         None => panic!("error: connect expects a service to be provided."),
        //     };
        //     handler.connect(service);
        // }
        "list" => {
            // Supported if the helper has the "fetch" or "import" capability.
            info!("Listing the references");
            let references = handler.list_references();
            for reference in references {
                println!("{} {}", reference.hash, reference.name);
            }
            println!();
        }

        "fetch" => {
            // This possibly should keep looping until all objects are fetched.
            let hash = match command_components.next() {
                Some(hash) => hash,
                None => panic!("error: fetch expects the hash to fetch to be provided."),
            };
            let name = match command_components.next() {
                Some(name) => name,
                None => panic!("error: fetch expects the name to be provided."),
            };
            info!("Fetching {} for '{}'.", hash, name);
            handler.fetch_object(hash, name);
        }
        "push" => {
            // A batch sequence of one or more push commands is terminated with a blank line (if
            // there is only one reference to push, a single push command is followed by a blank
            // line).
            //
            // The above batch sequence is not handled.

            let argument = match command_components.next() {
                Some(argument) => argument,
                None => panic!("error: push expects the source and destination to be provided."),
            };

            // If it starts with a + then it is a force update.
            let force_update = argument.starts_with("+");
            if let Some((source, destination)) = argument.split_once(":") {
                let source_cleaned = if force_update {
                    source[1..].to_string()
                } else {
                    source.to_string()
                };
                info!(
                    "Pushing references: {} to {}, force_update={}",
                    source_cleaned, destination, force_update
                );
                handler.push(source_cleaned.as_str(), destination, force_update);
            } else {
                panic!(
                    "error: push expects the source and destination to be provided separated by :"
                );
            }
        }
        _ => error!("error: remote-base: unknown command '{}' from git", command),
    }
    return true;
}
