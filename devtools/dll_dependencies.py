"""Using Dependencies by lucasg find dependencies of a set of DLLs.

Build a graph of those dependencies.
"""

import enum
import json
import os
import pathlib
import subprocess
import urllib.request
import zipfile

WORK_DIRECTORY = pathlib.Path("work_area")
TOOL_DOWNLOAD_URI = "https://github.com/lucasg/Dependencies/releases/download/v1.11.1/Dependencies_x64_Release.zip"
GRAPHVIZ_DOWNLOAD_URI = "https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/10.0.1/windows_10_cmake_Release_Graphviz-10.0.1-win64.zip"


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
                [
                    os.fspath(tool_exe),
                    "-json",
                    "-depth", "2",
                    "-chain", os.fspath(dll),
                ],
                text=True,
            )

            if cache_result:
                with cache_result_path.open("w") as writer:
                    writer.write(output)

            chain_as_json = json.loads(output)

        graph = _dependencies_chain_to_graph(chain_as_json)
        graphs.append(graph)

    return Graph.merge(graphs)


class GraphOutputType(enum.Enum):
    DOT = 1
    """DOT format with the layout computed."""

    PNG = 2
    """Portable network graphics, a raster format."""


def render_graph(
    graph: Graph,
    output_type: GraphOutputType,
    output_path: pathlib.Path,
    work_directory: pathlib.Path,
    *,
    perform_transitive_reduction: bool = False,
) -> pathlib.Path:
    """Render the given graph to an image with GraphViz.

    If perform_transitive_reduction is True, then the graph input is ran
    through GraphViz's tred tool to perform a transitive reduction.)
    """

    def _setup_tooling() -> pathlib.Path:
        work_directory.mkdir(exist_ok=True)

        tool_zip = work_directory / "graphviz.zip"
        if not tool_zip.exists():
            urllib.request.urlretrieve(GRAPHVIZ_DOWNLOAD_URI, filename=tool_zip)
        executable = work_directory / "Graphviz-10.0.1-win64" / "bin" / "dot.exe"
        if not executable.is_file():
            with zipfile.ZipFile(tool_zip) as opened_zip:
                opened_zip.extractall(work_directory)
        return executable

    dot_exe = _setup_tooling()
    tred_exe = dot_exe.parent / "tred.exe"

    if perform_transitive_reduction:
        process = subprocess.Popen(
            [
                os.fspath(tred_exe),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        graph.to_dot(process.stdin)

        process.stdin.close()

        post_tred_dot = ''.join(process.stdout)
        process.wait()
        process.stdout.close()
        if process.returncode:
            raise subprocess.CalledProcessError(process.returncode, process.args)


    type_to_format = {
        GraphOutputType.DOT: "dot",
        GraphOutputType.PNG: "png",
    }

    # This could be based purely on the output_path suffix.
    target_format = type_to_format[output_type]

    process = subprocess.Popen(
        [
            os.fspath(dot_exe),
            f"-T{target_format}",
            "-o",
            os.fspath(output_path),
        ],
        stdin=subprocess.PIPE,
        encoding="utf-8",
    )

    if perform_transitive_reduction:
        process.stdin.write(post_tred_dot)
    else:
        graph.to_dot(process.stdin)
    process.stdin.close()
    process.wait()

    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, process.args)

    return output_path


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
        return (
            exclude_system_dlls
            and depend["Filepath"]
            and depend["Filepath"].startswith("C:\\Windows\\")
        )

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

    render_graph(
        graph,
        GraphOutputType.PNG,
        work_directory / "example.png",
        work_directory,
    )

    render_graph(
        graph,
        GraphOutputType.PNG,
        work_directory / "example_post_tred.png",
        work_directory,
        perform_transitive_reduction=True,
    )

    # This version is used by graph_dependencies.html.
    render_graph(
        graph,
        GraphOutputType.DOT,
        work_directory / "depends.dot",
        work_directory,
        perform_transitive_reduction=True,
    )

    with (work_directory / "depend.dot").open("w") as writer:
        graph.to_dot(writer)
    with (work_directory / "depend.json").open("w") as writer:
        json.dump(graph.to_gephi_json(), writer)
    return graph


# Considerations:
# - Instead of relying on GraphViz's tred program, use NetworkX instead:
#   https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.transitive_reduction.html

if __name__ == "__main__":
    # TODO: Since this can now fetch GraphViz, that could be used here as the
    # example.
    example(pathlib.Path(r"D:\Programs\Development\Graphviz\bin"))
