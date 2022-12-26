# setup.py
from distutils.core import setup
import py2exe


setup(
    version = "0.7.1",
    description = "Covers",
    name = "Covers",
    # targets to build
    console = ["cccovers.py"],
    #zipfile = "lib/shared.zip",
    zipfile = "shared.lib",
    )

