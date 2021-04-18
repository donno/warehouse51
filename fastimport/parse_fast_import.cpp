//===----------------------------------------------------------------------===//
// Parses Git 'fast-import' format as documented here:
// https://www.git-scm.com/docs/git-fast-import#_input_format
//
// COPYRIGHT    : (c) 2021 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
//===----------------------------------------------------------------------===//

#include "parse_fast_import.hpp"

#include <charconv>
#include <fstream>
#include <functional>
#include <iostream>
#include <memory>
#include <optional>

#ifdef _MSC_VER
#include <fcntl.h>
#include <io.h>
#endif

//===----------------------------------------------------------------------===//
// Internal functions.
//===----------------------------------------------------------------------===//

void print_summarise(const FastImport::Commit& commit)
{
    // Output a quick summary.
    std::cout << "COMMIT called for ref: " << commit.myReference;
    if (commit.myMark)
    {
        std::cout << " has a mark of " << *commit.myMark;
    }

    if (commit.myMerges.size() == 1)
    {
        std::cout << " and has 1 merge";
    }
    else if (!commit.myMerges.empty())
    {
        std::cout << " and has " << commit.myMerges.size() << " merges";
    }

    if (commit.myFrom)
    {
        std::cout << " from " << *commit.myFrom << std::endl;
    }
    else
    {
        std::cout << std::endl;
    }
}

std::pair<std::unique_ptr<char[]>, std::size_t> parse_data(
    const std::string &command_line,
    std::istream &input)
{
    if (command_line.rfind("data ", 0) == 0)
    {
        auto countStart = command_line.c_str() + 5;
        auto countEnd = command_line.c_str() + command_line.size();
        std::size_t count;
        if (auto [p, ec] = std::from_chars(countStart, countEnd, count);
            ec == std::errc())
        {
            auto contents = std::make_unique<char[]>(count);
            input.read(contents.get(), count);
            return std::pair(std::move(contents), count);
        }
        else
        {
            std::cerr << "Failed to parse data count (size)." << std::endl;
            std::abort();
        }
    }
    else
    {
        std::cerr << "expected data command" << std::endl;
        std::abort();
    }
}

// Parse a mark which is of the form: 'mark' SP ':' <idnum> LF
std::optional<std::size_t> parse_mark(const std::string& line)
{
    if (line.rfind("mark :", 0) == 0)
    {
        // Now read the mark ID.
        std::size_t idNumber;

        auto idStart = line.c_str() + 6;
        auto idEnd = line.c_str() + line.size();
        if (auto [p, ec] = std::from_chars(idStart, idEnd, idNumber);
            ec == std::errc())
        {
            if (p != idEnd)
            {
                std::cerr << "Expected line feed after idnum for mark."
                          << std::endl;
            }

            return idNumber;
        }
        else
        {
            std::cerr << "Failed to parse mark for blob. This is being "
                         "treated as if there was no mark."
                      << std::endl;
        }
    }

    return std::nullopt;
}

//===----------------------------------------------------------------------===//
// Public functions defintions.
//===----------------------------------------------------------------------===//

FastImport::InvalidCommand::InvalidCommand(const std::string& command)
    : std::runtime_error("Unrecognised command. \"" + command + "\""),
      myCommand(command)
{
}

FastImport::Command FastImport::parse_command(const std::string& line)
{
    const auto commands = {
        "commit", "tag", "reset", "blob", "alias", "checkpoint", "progress",
        "done", "get-mark", "cat-blob", "ls", "feature", "option"};

    auto spaceIndex = line.find(' ');

    const auto command_word =
        spaceIndex == std::string::npos ? line : line.substr(0, spaceIndex);

    const auto command = std::find(std::begin(commands), std::end(commands),
                                   command_word);
    if (command == std::end(commands))
    {
        throw InvalidCommand(line);
    }

    return static_cast<Command>(std::distance(std::begin(commands), command));
}

FastImport::Blob FastImport::parse_blob(std::istream& input)
{
    std::string line;
    std::getline(input, line);

    Blob blob;

    // If there is no mark, then based on the documentation, it is expected the
    // correpsonding Git SHA-1 of the blob is referenced later in the commits.
    //
    // A future improvement would be to have this produce the SHA-1.
    blob.myMark = parse_mark(line);
    if (blob.myMark)
    {
        // The current line has been handled so read the next line.
        std::getline(input, line);
    }

    // 'original-oid' SP <object-identifier> LF
    if (line.rfind("original-oid ", 0) == 0)
    {
        // This provides the name of the object in the original source control
        // system.
        blob.myOriginalObjectIdentifier = line.substr(13);
        std::getline(input, line);
    }

    // 'data' SP <count> LF
    // <raw> LF? (the trailing LF is not included in <count>.).
    if (line.rfind("data ", 0) == 0)
    {
        auto [contents, count] = parse_data(line, input);
        blob.myData = std::move(contents);
        blob.myDataSize = count;

        if (input.peek() == '\n')
        {
            input.ignore(1);
        }
    }

    return blob;
}

FastImport::Reset FastImport::parse_reset(
    const std::string& command_line,
    std::istream& input)
{
    // 'reset' SP <ref> LF
    // ('from' SP <commit - ish> LF) ?
    //  LF ?

    Reset reset;
    reset.myReference = command_line.substr(6);;

    if (input.peek() == 'f')
    {
        std::string line;
        std::getline(input, line);
        if (line.rfind("from ", 0) == 0)
        {
            reset.myFrom = line.substr(5);
        }
    }

    // Account for final blank line.
    if (input.peek() == '\n')
    {
        input.ignore(1);
    }

    return reset;
}

//===----------------------------------------------------------------------===//
// Functions that need promoted to being public or internal.
//===----------------------------------------------------------------------===//

FastImport::Commit FastImport::parse_commit(
    const std::string& command_line,
    std::istream& input)
{
    // 'commit' SP <ref> LF
    // mark ?
    // original - oid ?
    // ('author' (SP <name>) ? SP LT <email> GT SP <when> LF) ?
    // 'committer' (SP <name>) ? SP LT <email> GT SP <when> LF
    // ('encoding' SP <encoding>) ?
    // data
    // ('from' SP <commit - ish> LF) ?
    // ('merge' SP <commit - ish> LF) *
    // (filemodify | filedelete | filecopy | filerename | filedeleteall | notemodify) *
    // LF ?

    std::string line;
    std::getline(input, line);

    Commit commit;
    commit.myReference = command_line.substr(7);
    commit.myMark = parse_mark(line);

    if (commit.myMark)
    {
        // The current line has been handled as it contained the mark so read
        // the next line.
        std::getline(input, line);
    }

    if (line.rfind("original-oid ", 0) == 0)
    {
        // This provides the name of the object in the original source control
        // system.
        commit.myOriginalObjectIdentifier = line.substr(13);
        std::getline(input, line);
    }

    if (line.rfind("author ", 0) == 0)
    {
        // 'author' (SP <name>)? SP LT <email> GT SP <when> LF)
        //std::cout << "AUTHOR LINE " << line << std::endl;
        std::getline(input, line);
    }

    if (line.rfind("committer ", 0) == 0)
    {
        // 'committer' (SP <name>) ? SP LT <email> GT SP <when> LF
        //
        // name may not contain LT, GT, LF.
        //std::cout << "committer LINE " << line << std::endl;
        std::getline(input, line);
    }
    else
    {
        std::cerr << "Expected a committer." << std::endl;
        std::abort();
    }

    if (line.rfind("encoding ", 0) == 0)
    {
        std::cout << "encoding - NYI: " << line << std::endl;
        std::getline(input, line);
    }

    // Read the data of the commit which is the commit message.
    auto [commitMessage, messageLength] = parse_data(line, input);
    commit.myCommitMessage.assign(
        commitMessage.get(), commitMessage.get() + messageLength);
    commitMessage.reset();

    // ('from' SP <commit - ish> LF) ?
    if (input.peek() == 'f')
    {
        std::getline(input, line);
        if (line.rfind("from ", 0) == 0)
        {
            commit.myFrom = line.substr(5);
        }
    }

    // ('merge' SP <commit - ish> LF) *
    while (input.peek() == 'm')
    {
        std::getline(input, line);
        if (line.rfind("merge ", 0) == 0)
        {
            commit.myMerges.push_back(line.substr(6));
        }
    }

    // Deal with the file commands which are:
    // filemodify = 'M' SP <mode> SP <dataref> SP <path> LF
    // filedelete = 'D' SP <path> LF
    // filecopy = 'D' SP <path> LF
    // filerename = 'R' SP <path> SP <path> LF
    // filedeleteall = 'deleteall' LF
    // notemodify = 'N' SP <dataref> SP <commit-ish> LF
    //
    // If dataref is inline then filemodify and notemodify contain data after.
    //
    // The deleteall directive will be given by `git fast-export --full-tree`.
    bool outOfFileCommands = false;
    do
    {
        switch (input.peek())
        {
        case 'D':
            std::getline(input, line);
            //std::cout << "File delete" << std::endl;
            break;
        case 'M':
            std::getline(input, line);
            //assert(input[1] == ' ');
            //std::cout << "File modification " << line.substr(2) << std::endl;
            break;
        case 'C':
            std::getline(input, line);
            //std::cout << "File copy" << std::endl;
            break;
        case 'R':
            std::getline(input, line);
            //std::cout << "File rename" << std::endl;
        case 'd':
            std::getline(input, line);
            //std::cout << "Maybe delete all" << std::endl;
            break;
        case 'N':
            std::getline(input, line);
            //std::cout << "Note modify" << std::endl;
            break;
        default:
            outOfFileCommands = true;
            break;
        }
    } while (!outOfFileCommands);

    // Account for final blank line.
    if (input.peek() == '\n')
    {
        input.ignore(1);
    }

    return commit;
}

void parse_progres(const std::string& command_line)
{
    if (command_line.rfind("progress ", 0) == 0)
    {
        // 'progress' SP <any> LF
        std::cout << "Progress status: " << command_line.substr(9)
                  << std::endl;
    }
    else
    {
        std::cerr << "Expected progress" << std::endl;
    }
}

static void convert_stdin_to_binary()
{
    // While discouraged, its still possible for binary files to be committed.
    //
    // The following is appliable to Windows.
    // https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/setmode
#ifdef _MSC_VER
    if (::_setmode(::_fileno(stdin), _O_BINARY) == -1)
    {
        std::cerr << "failed to change standard input to be binary. "
                  << "If there are binary files in the import it may fail."
                  << std::endl;
    }
#endif
}

int main(int argc, const char *argv[])
{
    std::ifstream file;
    if (argc == 2)
    {
        file.open(argv[1], std::ios::binary);
        if (!file.is_open())
        {
            std::cerr << "failed to open file" << std::endl;
            return 1;
        }
    }

    auto& input = file.is_open() ? file : std::cin;

    if (!file.is_open())
    {
        convert_stdin_to_binary();
    }

    const bool verbose = true;

    std::string command_line;
    while (std::getline(input, command_line))
    {
        switch (FastImport::parse_command(command_line))
        {
        case FastImport::Command::Blob:
        {
            const FastImport::Blob blob = FastImport::parse_blob(input);
            if (verbose)
            {
                std::cout << "Blob " << *blob.myMark << " with "
                          << blob.myDataSize
                          << " bytes." << std::endl;
            }
            break;
        }
        case FastImport::Command::Reset:
        {
            const auto reset = FastImport::parse_reset(command_line, input);
            if (verbose)
            {
                std::cout << "reset [" << reset.myReference << "]" << std::endl;
            }
            break;
        }
        case FastImport::Command::Commit:
        {
            const auto commit = FastImport::parse_commit(command_line, input);
            if (verbose)
            {
                print_summarise(commit);
            }
            break;
        }
        case FastImport::Command::Progress:
            parse_progres(command_line);
            if (input.peek() == '\n') input.ignore(1);
            break;
        case FastImport::Command::Feature:
        {
            std::cerr << "Feature support is not implemented." << std::endl;
            return 3;
        }
        default:
            std::cerr << "Unimplemented command: " << command_line
                    << std::endl;
            return 2;
        }
    }

    if (verbose) std::cout << "DONE." << std::endl;

    return 0;
}
