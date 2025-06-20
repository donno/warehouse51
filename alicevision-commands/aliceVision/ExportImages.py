__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ExportImages(desc.AVCommandLineNode):
    commandLine = 'aliceVision_exportImages {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=40)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Export'
    documentation = '''
    Export images referenced in the input sfmData by transforming 
    them to adapt to the required target intrinsics. For example, the target
    intrinsics may be the same without the distortion.
    '''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file. Contains the original intrinsics of the images.",
            value="",
        ),
        desc.File(
            name="target",
            label="Target",
            description="This sfmData file contains the required intrinsics for the output images.",
            value="",
        ),
        desc.ChoiceParam(
            name="outputFileType",
            label="Output File Type",
            description="Output file type for the exported images.",
            value="exr",
            values=["jpg", "png", "tif", "exr"],
            advanced=True,
        ),
        desc.BoolParam(
            name="evCorrection",
            label="Correct Images Exposure",
            description="Apply a correction on images' exposure value.",
            value=False,
            advanced=True,
        ),
        desc.ChoiceParam(
            name="namingMode",
            label="Naming mode",
            description="image naming mode :\n"
                        " - viewid: viewid.ext.\n"
                        " - frameid: Frameid.ext.\n"
                        " - keep: Keep original name.\n",
            value="frameid",
            values=["viewid", "frameid", "keep"],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="masksFolder",
                label="Masks Folder",
                description="",
                value="",
            ),
            name="masksFolders",
            label="Masks Folders",
            description="Use masks from specific folder(s). Filename should be the same or the image UID.",
        ),
        desc.ChoiceParam(
            name="maskExtension",
            label="Mask Extension",
            description="File extension for the masks to use.",
            value="png",
            values=["exr", "jpg", "png"],
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Images Folder",
            description="Output folder.",
            value="{nodeCacheFolder}",
        ),
        desc.File(
            name="undistorted",
            label="Undistorted Images",
            description="List of undistorted images.",
            semantic="image",
            value="{nodeCacheFolder}/<VIEW_ID>.{outputFileTypeValue}",
            group="",
            advanced=True,
        ),
    ]
