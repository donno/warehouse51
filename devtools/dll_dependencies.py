"""Using Dependencies by lucasg find dependencies of a set of DLLs.

Build a graph of those dependencies.
"""

import json
import os
import pathlib
import subprocess
import urllib.request
import zipfile

WORK_DIRECTORY = pathlib.Path("work_area")
TOOL_DOWNLOAD_URI = "https://github.com/lucasg/Dependencies/releases/download/v1.11.1/Dependencies_x64_Release.zip"


class Graph:
    """Represent a directed graph of nodes and edges between nodes."""

    def __init__(self) -> None:
        self.nodes = set()
        self.edges = []

    def add_node(self, node):
        """Add the node to the graph."""
        self.nodes.add(node)

    def add_edge(self, from_node, to_node):
        """Add a directed edge between the two given nodes."""
        if from_node == to_node:
            # Maybe log that.
            return
        self.edges.append((from_node, to_node))

    def __str__(self):
        """Summaries the graph's content."""
        return f"Graph(nodes={len(self.nodes)}, edges={len(self.edges)})"

    def to_dot(self, writer):
        """Write to dot format to the writer."""
        writer.write("digraph g {\n")

        # TODO: Nodes don't have any extra label at this moment or colouring
        # so no need to output it.
        for source, target in self.edges:
            writer.write(f'      "{source}" -> "{target}";\n')
        writer.write("}")

    def to_gephi_json(self) -> dict:
        """Convert to the graph to Gephi's JSON format.

        This may actually be the Sigma.js format that Gephi used.
        """
        # Consider using dot instead to layout the nodes (assign X/Y).
        node_to_id = {node: str(node_id) for node_id, node in enumerate(self.nodes)}
        return {
            "edges": [
                {
                    "source": node_to_id[source],
                    "target": node_to_id[target],
                }
                for source, target in self.edges
            ],
            "nodes": [
                # "color": "rgb(229,67,164)",
                {"label": node, "id": str(node_id)}
                for node_id, node in enumerate(self.nodes)
            ],
        }

    @classmethod
    def merge(cls, graphs: list):
        """Merge the given graphs together, deduplicating nodes and edges."""
        merged_graph = cls()
        for graph in graphs:
            merged_graph.nodes.update(graph.nodes)
            merged_graph.edges.extend(
                edge for edge in graph.edges if edge not in merged_graph.edges
            )
        return merged_graph


def find_dependencies(
    dlls: list[pathlib.Path],
    work_directory: pathlib.Path,
    *,
    cache_result: bool = True,
) -> Graph:
    """Find dependencies between libraries.

    If cache_result is True then the results look-up of the dependencies will
    be cached and used if cached.

    The caching feature is purely done based on file-name so its not suitable
    if you comparing different versions. This could be expended to compute the
    hash of the source DLL and include that in the filename or go nested
    in the form filename/<hash>.json if multi-versions of DLL is likely.
    """
    # Options:
    # 1) Use Rust code to read the DLLs and extract the information
    # 2) Rely on "dumpbin /dependents" and read output
    # 3) Reply on Dependencies.exe (by lucasg) and use:
    #   - Dependencies.exe -chain mydll.dll -depth 1
    # 40 Read the information straight from the DLL here - this requires a
    #    third party package.
    #
    # This has used the 3rd option.

    def _setup_tooling() -> pathlib.Path:
        work_directory.mkdir(exist_ok=True)

        tool_zip = work_directory / "Dependencies_x64_Release.zip"
        if not tool_zip.exists():
            urllib.request.urlretrieve(TOOL_DOWNLOAD_URI, filename=tool_zip)

        executable = work_directory / "Dependencies" / "Dependencies.exe"
        if not executable.is_file():
            with zipfile.ZipFile(tool_zip) as opened_zip:
                opened_zip.extractall(executable.parent)
        return executable

    tool_exe = _setup_tooling()

    graphs = []

    for dll in dlls:
        cache_result_path = work_directory / dll.with_suffix(".json").name

        if cache_result and cache_result_path.exists():
            with cache_result_path.open("r") as reader:
                chain_as_json = json.load(reader)
        else:
            output = subprocess.check_output(
                [os.fspath(tool_exe), "-json", "-depth", "2", "-chain", os.fspath(dll)],
                text=True,
            )

            if cache_result:
                with cache_result_path.open("w") as writer:
                    writer.write(output)

            chain_as_json = json.loads(output)

        graph = _dependencies_chain_to_graph(chain_as_json)
        graphs.append(graph)

    return Graph.merge(graphs)


def _dependencies_chain_to_graph(
    chain_json: dict,
    *,
    exclude_system_dlls: bool = True,
) -> Graph:
    """Generate list of nodes and edges for dot.

    chain_json is expected to come from the -json and -chain options of
    Dependencies by lucasg.
    """
    dependencies_to_check = [chain_json["Root"]]

    def _exclude_depend(depend: dict):
        return (exclude_system_dlls
                and depend["Filepath"]
                and depend["Filepath"].startswith("C:\\Windows\\"))

    graph = Graph()
    visited = set()
    while dependencies_to_check:
        current = dependencies_to_check.pop()
        if current["ModuleName"] in visited:
            continue
        visited.add(current["ModuleName"])
        graph.add_node(current["ModuleName"])
        for depend in current["Dependencies"]:
            if not _exclude_depend(depend):
                graph.add_node(depend["ModuleName"])
                graph.add_edge(current["ModuleName"], depend["ModuleName"])
                dependencies_to_check.append(depend)

    return graph


def example(directory: pathlib.Path) -> Graph:
    """Provides an example of using this module."""
    work_directory = WORK_DIRECTORY
    dlls = [entry for entry in directory.iterdir() if entry.name.endswith(".dll")]
    graph = find_dependencies(dlls, work_directory)

    with (work_directory / "depend.dot").open("w") as writer:
        graph.to_dot(writer)
    with (work_directory / "depend.json").open("w") as writer:
        json.dump(graph.to_gephi_json(), writer)
    return graph


# Considerations:
# - Intergrate graphviz to use its tred (transitive reduction program) as for
#   DLLs which have lots of reuse the graphs can become very busy.
#   Or use NetworkX:
#   https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.transitive_reduction.html

if __name__ == "__main__":
    example(pathlib.Path(r"D:\Programs\Development\Graphviz\bin"))
