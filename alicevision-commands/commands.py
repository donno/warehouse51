"""Extract commands from AliceVision's Python package.

This needs the aliceVision package from https://github.com/alicevision/AliceVision/tree/develop/meshroom
which has been vendored in for now. The release doesn't contain that.
"""

# This module is available under the MIT licence as well as MPL-2.0.

import collections.abc
import importlib
import inspect
import pathlib
import pkgutil
import string

# AV is the AliceVision specific command lines.
# There is also CommandLineNode which is generic.
from meshroom.core.desc.node import AVCommandLineNode
from meshroom.core.desc.attribute import Attribute


SCRIPT_DIRECTORY = pathlib.Path(__file__).parent
"""The directory containing this script."""

PACKAGE_NAME = "aliceVision"
"""The name of the package to import"""

class Command:
    """Represent a command in AliceVision/Meshroom.

    A command has a inputs and outputs.
    """

    def __init__(self, command: AVCommandLineNode) -> None:
        """Construct a command from the command line node."""
        self.raw = command
        """The raw version of the command from meshroom."""

    @property
    def category(self) -> str:
        """Defines the classification of the given command.

        This allows similar commands to be grouped together.
        """
        return self.raw.category

    @property
    def name(self) -> str:
        """The name of the command."""
        return self.raw.__name__

    @property
    def inputs(self) -> list[Attribute]:
        """The list of inputs for the command."""
        return self.raw.inputs

    @property
    def outputs(self) -> list[Attribute]:
        """The list of outputs for the command."""
        return self.raw.outputs

    def __repr__(self):
        return f'Command("{self.name}")'

    def __str__(self) -> str:
        def format_attribute(attr: Attribute) -> str:
            """Format the attribute for a simply summary."""
            return f"{attr.label} [{attr.name}] {attr.type}\n\t{attr.description}\n"

        command = self
        return (
            f"[{command.category}].{command.name}\n"
            + "\n".join(format_attribute(attr) for attr in command.inputs)
            + "\n".join(format_attribute(attr) for attr in command.outputs)
        )


def modules(package_path: pathlib.Path) -> collections.abc.Generator[Command]:
    """Return the modules in package at the given path."""
    for module_information in pkgutil.walk_packages(
        [package_path],
        package_path.name + ".",
    ):
        module = importlib.import_module(module_information.name)
        yield module


def commands(modules: collections.abc.Iterable) -> collections.abc.Generator[Command]:
    """Return the AliceVision commands in the given modules."""
    for module in modules:
        if not inspect.ismodule(module):
            message = "Expected a module."
            raise TypeError(message)
        for _, klass in inspect.getmembers(module, inspect.isclass):
            if issubclass(klass, AVCommandLineNode):
                yield Command(klass)


def alice_commands() -> collections.abc.Generator[Command]:
    """Yield the commands from AliceVision."""
    yield from commands(modules(SCRIPT_DIRECTORY / PACKAGE_NAME))


def parameters_for_command_line(command: Command) -> list:
    """Determine the parameters required for a the command line of a command."""
    return _parameters_for_command_line(command.raw.commandLine)


def _parameters_for_command_line(command_line: str) -> list:
    """Determine the parameters referred to by the command line.

    Examples
    --------
    >>> _parameters_for_command_line("hello {name}")
    ['name']
    >>> _parameters_for_command_line("example --size={size} --cores={cores}")
    ['size', 'cores']
    """
    parameters = []
    parsed_format = string.Formatter().parse(command_line)
    for literal_text, field_name, format_spec, conversion in parsed_format:
        if conversion is not None:
            # This case may need to be handled once there is an example of it.
            raise ValueError("Expected conversion to be None.")
        if format_spec:
            # This case may need to be handled once there is an example of it.
            raise ValueError("Expected format_spec to be None.")
        if field_name:
            parameters.append(field_name)
    return parameters


def main() -> None:
    """Output a summary of each command found in the aliceVision package."""
    for command in alice_commands():
        print(f"{command}\n{'=' * 32}")

        # Test parameters_for_command_line with every command.
        _ = parameters_for_command_line(command)


if __name__ == "__main__":
    main()
