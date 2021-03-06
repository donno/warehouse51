//===----------------------------------------------------------------------===//
//
// NAME         : apply
// SUMMARY      : Applies a list of removals to a graph.
// COPYRIGHT    : (c) 2108 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
// DESCRIPTION: : Using a list of edges to remove from a graph, this applies
//                the changes to the graph.
//
//===----------------------------------------------------------------------===//

#include <boost/algorithm/string/trim.hpp>

#include <algorithm>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

// Read the edge removal list from input stream.
//
// The file is formatted as: Remove:Edge:<EdgeA>:<EdgeB>
//
// The output is formatted to be of the form: "<EdgeA>" -> "<EdgeB>";
//
// This matches the exact formatting of an edge line in the DOT files that
// these tools were originally written for, sans leading whitespace.
std::vector<std::string> read_removal_list(std::istream& input)
{
    const std::string removeDirective("Remove:Edge:");

    std::vector<std::string> removalList;
    for (std::string line; std::getline(input, line);)
    {
        if (line.compare(0, removeDirective.length(), removeDirective) == 0)
        {
            const auto split = line.find(':', removeDirective.length());
            removalList.push_back(
                "\"" +
                line.substr(removeDirective.length(),
                            split - removeDirective.length()) +
                "\" -> \"" + line.substr(split + 1) + "\";");
        }
        else
        {
            std::cerr << "Unknown directive." << line << std::endl;
        }
    }

    // Ensure its sorted so we can binary search on it.
    std::sort(removalList.begin(), removalList.end());
    return removalList;
}

void apply_removal_list(const std::vector<std::string>& removals,
                        std::istream& graph)
{
    // Algorithm:
    // - Read each line from the graph
    //   - Check if the line matches a line in the removal list.
    //   - If it doesn't write out the line.
    //
    // This only works because the script expects a strict dot/graphviv file
    // (i.e where the edges are a specific indentation and the node names are
    // quoted).
    std::cerr << "Edge to remove: " << removals.front() << std::endl;
    for (std::string line; std::getline(graph, line);)
    {
        auto trimmedLine = line;
        boost::algorithm::trim(trimmedLine);
        if (std::binary_search(removals.begin(), removals.end(), trimmedLine))
        {
            std::cerr << "Removed edge" << std::endl;
        }
        else
        {
            std::cout << line << std::endl;
        }
    }
}

int main(int argc, const char* argv[])
{
    std::istream* input = &std::cin;
    std::fstream inputFile;
    std::fstream removalFile;
    if (argc < 2)
    {
        std::cerr << "usage: " << argv[0] << " removal_file [dot file]"
                  << std::endl;
        return 1;
    }
    else if (argc == 2)
    {
        removalFile.open(argv[1], std::fstream::in);
        if (!removalFile)
        {
            std::cerr << "Failed to open file" << std::endl;
            return 1;
        }

        // The input stream already points to standard in.
    }
    else if (argc == 3)
    {
        removalFile.open(argv[1], std::fstream::in);
        if (!removalFile)
        {
            std::cerr << "Failed to open file" << std::endl;
            return 1;
        }

        inputFile.open(argv[2], std::fstream::in);
        if (!inputFile)
        {
            std::cerr << "Failed to open file" << std::endl;
            return 1;
        }
        input = &inputFile;
    }

    const auto removals = read_removal_list(removalFile);
    std::cerr << "There are " << removals.size() << " possible removals."
              << std::endl;
    apply_removal_list(removals, *input);
    return 0;
}
