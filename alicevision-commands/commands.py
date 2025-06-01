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


def main() -> None:
    """Output a summary of each command found in the aliceVision package."""
    for command in alice_commands():
        print(f"{command}\n{'=' * 32}")


if __name__ == "__main__":
    main()
