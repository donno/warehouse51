//===----------------------------------------------------------------------===//
//
// NAME         : dedupe
// SUMMARY      : Removes non-critical edges from a graph.
// COPYRIGHT    : (c) 2108 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
// DESCRIPTION: : Reports the edges that should be removed from graph as they
//                are not along the critical path.
//
// It is designed for graphs which match the following criteria:
// - Effectively a tree.
// - Directed
// - No cycles
// - Multiple leaves/roots.
//
// The high level view goal is to keep the longest paths between two vertices
// and remove the short paths. It does this by determining which edges to
// remove and utilises another tool to apply the changes.
//
//===----------------------------------------------------------------------===//
//
// Development notes:
//   g++ -O3 -Wall -Wextra --std=c++1y dedupe.cpp -lboost_graph
//
// This tool makes use of the Boost.Graph library and the following link
// provides a good starting point.
// http://www.boost.org/doc/libs/1_66_0/libs/graph/doc/table_of_contents.html
//
// Possible options:
// - Use Floyd-Warshall algorithm  to find the shortest paths by assigning
//   negative weights so A -> C is considered -1 but A -> B ->C is considered
//   -2 so is shorter.
//
//===----------------------------------------------------------------------===//

#include <boost/graph/graphviz.hpp>
#include <boost/graph/topological_sort.hpp>

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

// Boost.Graph supports two ways defining how the properties of the graphs
// are set-up. The types using each method are defined in their own namespace,
// named after the method (way). Switching between the two is done at
// compile time.
namespace property_lists
{
    // The following graph uses uses property lists. From my reading these are
    // discouraged but are still supported for existing code.
    using vertex_p =
        boost::property<boost::vertex_name_t, std::string,
                        boost::property<boost::vertex_color_t, float>>;
    using edge_p = boost::no_property;
    using graph_t = boost::adjacency_list<boost::vecS, boost::vecS,
                                          boost::directedS, vertex_p, edge_p>;

    struct VertexToName
    {
        VertexToName(const graph_t& graph)
            : index_to_name(boost::get(boost::vertex_name, graph))
        {
        }

        std::string operator()(graph_t::vertex_descriptor vertex) const
        {
            return boost::get(index_to_name, vertex);
        }

        decltype(boost::get(boost::vertex_name,
                            std::declval<graph_t>())) index_to_name;
    };
}

namespace bundled_properties
{
    // The following graph uses bundled_properties.
    // http://www.boost.org/doc/libs/1_66_0/libs/graph/doc/bundles.html

    struct Vertex
    {
        std::string name;
    };

    // The graphs have no properties (all the edges have a  weights of 1
    // and they are never styled differently).
    struct Edge
    {
    };

    using graph_t = boost::adjacency_list<boost::vecS, boost::vecS,
                                          boost::directedS, Vertex, Edge>;

    struct VertexToName
    {
        VertexToName(const graph_t& graph) : graph(graph) {}

        std::string operator()(graph_t::vertex_descriptor vertex) const
        {
            return graph[vertex].name;
        }

      private:
        const graph_t& graph;
    };
}

#define USE_PROPERTY_LISTS
#ifdef USE_PROPERTY_LISTS
using graph_t = property_lists::graph_t;
using vertex_to_name_t = property_lists::VertexToName;
#else
using graph_t = bundled_properties::graph_t;
using vertex_to_name_t = bundled_properties::VertexToName;
#endif
using vertex_t = graph_t::vertex_descriptor;
using path_t = std::vector<graph_t::vertex_descriptor>;

// Set-up the properties for reading from a GraphViz file.
void setup_properties(property_lists::graph_t* graph,
                      boost::dynamic_properties* dp);
void setup_properties(bundled_properties::graph_t* graph,
                      boost::dynamic_properties* dp);

// Return the length of the longest path between u and v in graph.
std::size_t longest_path_length(const graph_t& graph, vertex_t u, vertex_t v);

// Returns the length of the first path between u and v in graph that is
// non-trival, that is to say is not simply the edge (u, v)
std::size_t length_first_non_trival_path(const graph_t& graph, vertex_t u,
                                         vertex_t v);

template <typename Report>
void all_paths_helper(vertex_t from, vertex_t to, graph_t const& g,
                      path_t& path, Report const& callback)
{
    path.push_back(from);

    if (from == to)
    {
        // Ideally we would check the result of callback if it had one
        // otherwise ignore it.
        callback(path);
    }
    else
    {
        for (auto out : make_iterator_range(out_edges(from, g)))
        {
            auto v = target(out, g);
            // The following statement would always be true in our graphs.
            // assert(path.end() == std::find(path.begin(), path.end(), v));
            all_paths_helper(v, to, g, path, callback);
        }
    }

    path.pop_back();
}

template <typename Report>
void all_paths(vertex_t from, vertex_t to, graph_t const& graph,
               Report const& callback)
{
    path_t state;
    all_paths_helper(from, to, graph, state, callback);
}

void setup_properties(property_lists::graph_t* graph,
                      boost::dynamic_properties* dp)
{
    boost::property_map<property_lists::graph_t, boost::vertex_name_t>::type
        name = boost::get(boost::vertex_name, *graph);
    dp->property("node_id", name);
}

void setup_properties(bundled_properties::graph_t* graph,
                      boost::dynamic_properties* dp)
{
    dp->property("node_id",
                 boost::get(&bundled_properties::Vertex::name, *graph));
}

std::size_t longest_path_length(const graph_t& graph, vertex_t u, vertex_t v)
{
    std::size_t longestPathLength = 0;
    all_paths(u, v, graph, [&](path_t const& path) {
        if (longestPathLength < path.size())
        {
            longestPathLength = path.size();
        }
    });
    return longestPathLength;
}

std::size_t length_first_non_trival_path(const graph_t& graph, vertex_t u,
                                         vertex_t v)
{
    // Assume there exists an edge from (u, v) otherwise this function
    // wouldn't have be called.
    std::size_t longestPathLength = 2;

    struct path_found_exception
    {
    };
    const auto callback = [&](path_t const& path) {
        if (longestPathLength < path.size())
        {
            longestPathLength = path.size();
            throw path_found_exception();
        }
    };

    path_t state;
    try
    {
        all_paths_helper(u, v, graph, state, callback);
    }
    catch (const path_found_exception&)
    {
    }

    return longestPathLength;
}

void find_edges_to_remove(const graph_t& graph)
{
    std::vector<int> topo_order(boost::num_vertices(graph));
    boost::topological_sort(graph, topo_order.rbegin());

    const vertex_to_name_t vertex_to_name(graph);

    // Next produce the combinations of the nodes.
    for (std::size_t i = 0; i < topo_order.size(); ++i)
    {
        for (std::size_t j = i + 1; j < topo_order.size(); ++j)
        {
            auto u = topo_order[i];
            auto v = topo_order[j];

            // The following is only required if there exists an edge from
            // u to v as otherwise there will be nothing to remove.
            const auto result = boost::edge(u, v, graph);

            if (!result.second) continue;

            // Find all the paths from u to v and take the longest.
            //
            // TODO: I think this really just needs to be find a path to
            // v that is longer than 2.
            if (longest_path_length(graph, u, v) > 2)
            {
                // Remove the short path as there is a longer path we must
                // travel to get to v.
                std::cout << "Remove:Edge:" << vertex_to_name(u) << ":"
                          << vertex_to_name(v) << std::endl;
            }
        }
    }
}

void find_edges_to_remove_v2(const graph_t& graph)
{
    // For each edge (u, v) or (source, target) in the graph:
    // - Determine if there exists a path from u to v that doesn't invovle the
    // edge.
    // - If there is such a path flag the edge for removal.

    // const auto limit = std::numeric_limits<std::size_t>::max();
    const auto edge_process_limit = 150;

    const vertex_to_name_t vertex_to_name(graph);
    const auto edge_count = boost::num_edges(graph);
    std::size_t current_edge = 0;
    for (const auto& edge : boost::make_iterator_range(boost::edges(graph)))
    {
        const auto& u = boost::source(edge, graph);
        const auto& v = boost::target(edge, graph);

        // Find if there exists a path from u to v that isn't just u -> v.
        if (length_first_non_trival_path(graph, u, v) > 2)
        {
            // Remove the short path as there is a longer path we must
            // travel to get to v.
            std::cout << "Remove:Edge:" << vertex_to_name(u) << ":"
                      << vertex_to_name(v) << std::endl;
        }
        ++current_edge;
        std::cerr << "Progress:Removal:" << current_edge << ":" << edge_count
                  << std::endl;
        if (current_edge > edge_process_limit)
        {
            std::cerr << "Progress:Removal:Reached limit:"
                      << edge_process_limit << std::endl;
            break;
        }
    }
}

int main(int argc, const char* argv[])
{
    std::fstream inputFile;
    if (argc == 2)
    {
        inputFile.open(argv[1], std::fstream::in);
    }
    else if (argc == 1)
    {
        // TODO: Use standard in here instead.
        inputFile.open("test_basic.dot", std::fstream::in);
    }
    else
    {
        std::cerr << "usage: " << argv[0] << " [dot file]" << std::endl;
        return 1;
    }

    if (!inputFile)
    {
        std::cerr << "Failed to open file" << std::endl;
        return 1;
    }

    graph_t graph(0);
    boost::dynamic_properties dp(boost::ignore_other_properties);
    setup_properties(&graph, &dp);
    bool status = boost::read_graphviz(inputFile, graph, dp, "node_id");
    if (!status)
    {
        std::cerr << "Failed to read file" << std::endl;
        return 1;
    }

    find_edges_to_remove_v2(graph);
    return 0;
}