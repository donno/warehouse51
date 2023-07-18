"""Pure-Python module for interacting with Nuget Server and packages.

This package is not intended to be used to create or publish packages.

Future ideas for this module is to:
- Load NuGet.Config
    - Determine what servers to download from
    - Determine where packages are cached
- Potentially support caching compatible with the nuget tool if that is
  practical.

The original idea of this module was to use Python.NET to load the
Nuget.Protocol however that involves too much bootstrapping and packages of it
own.
"""

# TODO: Rename this to nugetapi as PyNuGet is already a project on PyPi for a
# NuGet Server. 

import zipfile
import logging
import os
import urllib.parse
import xml.etree.ElementTree as ElementTree

import requests


class HTTPClient:
    """Accesses NuGet Server via HTTP."""

    INDEX_URI = 'https://api.nuget.org/v3/index.json'
    """The URI to the service index.

    The entry point for the API is a JSON document in a well known location.

    https://learn.microsoft.com/en-us/nuget/api/service-index
    """

    def __init__(self) -> None:
        self.session = requests.Session()
        self._index = None
        self._package_base_uri = None
        self._logger = logging.getLogger('pynuget.client')

    def index(self):
        """Retrieve the service index.

        See https://learn.microsoft.com/en-us/nuget/api/service-index for
        details.
        """
        if self._index:
            return self._index

        response = self.session.get(self.INDEX_URI)
        response.raise_for_status()
        index = response.json()
        self._index = index
        return index

    def package(self, name):
        """Retrieve the index for a given package.

        See Enumerate package versions for details at:
        https://learn.microsoft.com/en-us/nuget/api/package-base-address-resource
        """
        # TODO: Validate package ID (name)
        self._logger.info('Fetching package: %s', name)
        package_index = urllib.parse.urljoin(self._package_base_address(),
                                            name.lower() + '/index.json')
        response = self.session.get(package_index)
        response.raise_for_status()
        return response.json()

    def download_package(self, name, version, destination_folder):
        """Download a package with given name and version.

        See Download package content (.nupkg) for details at:
        https://learn.microsoft.com/en-us/nuget/api/package-base-address-resource
        """
        # https://learn.microsoft.com/en-us/nuget/api/package-base-address-resource
        self._logger.info('Fetching package: %s @ version %s', name, version)
        filename = f'{name.lower()}.{version.lower()}.nupkg'
        target = os.path.join(destination_folder, filename)

        if os.path.isfile(target):
            return target

        package = urllib.parse.urljoin(
            self._package_base_address(),
            f'{name.lower()}/{version.lower()}/{filename}')

        # TODO: download to temp file then rename.
        response = requests.get(package, stream=True)
        with open(target, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
        return target

    def _package_base_address(self):
        if self._package_base_uri:
            return self._package_base_uri
        index = self.index()
        resource_type = 'PackageBaseAddress/3.0.0'
        resource = next(resource for resource in index['resources']
                        if resource['@type'] == resource_type)
        self._package_base_uri = resource['@id']
        return self._package_base_uri

def dependencies_from_nupkg(path, framework):
    """Read dependencies from a nupkg.

    framework must be one of the supported frameworks, with examples being:
    - .NETFramework4.7.2
    - .NETStandard2.0
    - net5.0
    """
    with zipfile.ZipFile(path, 'r') as archive:
        nuspec_info = next(
            info for info in archive.infolist()
            if info.filename.endswith('.nuspec'))
        with archive.open(nuspec_info) as nuspec_file:
            nuspec = ElementTree.parse(nuspec_file)

    namespaces = {
        'ns0': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd',
    }
    group_path = './/ns0:metadata/ns0:dependencies/ns0:group'

    frameworks_found = []
    for group in nuspec.getroot().findall(group_path, namespaces):
        if group.attrib['targetFramework'] == framework:
            break
        frameworks_found.append(group.attrib['targetFramework'])
    else:
        raise ValueError(
            f'Unable to find a match for framework: {framework} out of '
            f'{", ".join(frameworks_found)}')

    # This does not honour the exclude property.
    for dependency in group.findall('.//ns0:dependency', namespaces):
        yield dependency.attrib['id'], dependency.attrib['version']



def fetch_dependencies(client, package):
    """Download the dependencies for the package and their dependencies.
    """
    packages = [package]

    while packages:
        package = packages.pop()
        for depend in dependencies_from_nupkg(package,
                                              framework='.NETFramework4.7.2'):
            depend_id, depend_version = depend
            packages.append(
                client.download_package(depend_id, depend_version, 'downloads')
            )

if __name__ == '__main__':
    # This module is under development.
    #
    # At some point it might offer a CLI to allow download and extract.
    logging.basicConfig(level=logging.INFO)
    client = HTTPClient()
    #print(client.package('NuGet.Protocol'))
    package = client.download_package('NuGet.Protocol', '6.6.1', 'downloads')
    fetch_dependencies(client, package)
