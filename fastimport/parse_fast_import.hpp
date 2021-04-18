#ifndef FAST_IMPORT_PARSE_HPP
#define FAST_IMPORT_PARSE_HPP
//===----------------------------------------------------------------------===//
//
// NAME         : parse_fast_import
// SUMMARY      : Functions for parsing Git's fast-import format.
// COPYRIGHT    : (c) 2021 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
// DESCRIPTION: : Parses the output of git fast-export and other tools designed
//                to be used with git fast-import.
//
// The format is documented here:
// https://www.git-scm.com/docs/git-fast-import#_input_format
//
// The three commands that have been implemented: Commit, Blob, Reset are the
// commands that seem appear when using "git fast-export".
// Additional flags like --use-done-feature will change that.
//
//===----------------------------------------------------------------------===//

#include <iosfwd>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

namespace FastImport
{
    struct Blob;
    struct Reset;
    struct Commit;

    // Enumeration of the commands.
    // Commands commented with a * mean clients will announce if they send
    // this via the feature command.
    enum class Command
    {
        // Create or update a branch with a new commit, recording one logical
        // change to the project.
        Commit = 0,
        Tag,
        Reset,
        Blob,
        Alias,
        Checkpoint,
        Progress,
        Done, // * - Has a corresponding feature announcement.
        GetMark, // * - Has a corresponding feature announcement.
        CatBlob, // * - Has a corresponding feature announcement.
        Ls, // * - Has a corresponding feature announcement.

        // Enable the specified feature. If the parser does not support the
        // specified feature, then it should abort.
        Feature,

        Option,
    };

    // Exception raised when an invalid command is parsed.
    class InvalidCommand : public std::runtime_error
    {
    public:
        InvalidCommand(const std::string& command);

    private:
        std::string myCommand;
    };

    // Parse the the line containing a command. If it is not a valid command
    // then InvalidCommand will be throw.
    Command parse_command(const std::string& line);

    // If parse_command returns a Command::Blob then use this to parse the blob
    // data out.
    Blob parse_blob(std::istream& input);

    // If parse_command returns a Command::Reset then use this to parse the 
    // reset data. The line from parse_command needs to be passed in as
    // it contains the data.
    Reset parse_reset(const std::string& command_line, std::istream& input);

    // If parse_command returns a Command::Commit then use this to parse the 
    // commit data. The line from parse_command needs to be passed in as
    // it contains the inital information.
    Commit parse_commit(const std::string& command_line, std::istream& input);

    struct Blob
    {
        // A reference to this blob that can be referenced by other commands 
        // like commit.
        std::optional<std::size_t> myMark;
        
        // This may be provided and will be the the name of the object in the
        // original source control system.
        std::optional<std::string> myOriginalObjectIdentifier;

        // The contents of the blob.
        std::unique_ptr<const char[]> myData;

        // The number of bytes in myData.
        std::size_t myDataSize;
    };

    struct Reset
    {
        std::string myReference;
        std::optional<std::string> myFrom;
    };

    struct Person
    {
        std::string myName; // This will be empty if it is not provided.
        std::string myEmail;
        // when not implemented.

        // TODO: Consider storing the original line, and then having
        // name, email and when be subviews.
    };

    struct Commit
    {
        std::string myReference;

        // A reference to this mark that can be referenced by other commands 
        // like commit.
        std::optional<std::size_t> myMark;

        // This may be provided and will be the the name of the object in the
        // original source control system.
        std::optional<std::string> myOriginalObjectIdentifier;

        // Optional the author of the commit.
        std::optional<Person> myAuthor;
        
        // The committer of the commit.
        Person myCommitter;

        // The commit message.
        std::string myCommitMessage;

        // The commit-ish or reference where this commit comes from.
        std::optional<std::string> myFrom;

        // The commit-ish or reference that are part of the merge. This are
        // the additional parents.
        std::vector<std::string> myMerges;
    };
}

#endif
