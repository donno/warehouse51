"""Development playground for Virtual Machine related research and tooling."""

import enum
import hashlib
import json
import os
import pathlib
import requests
import logging

# Once 3.11 becomes old, then tomllib may be my go-to instead.
import configparser


CACHE_DIRECTORY = 'cache'

# Works well when developing as it eliminates even the conditional GET.
ALWAYS_USE_CACHE = True

class CoreOS:
    """Pseudo CoreOS namespace for related enumerations."""

    class Stream(str, enum.Enum):
        """There are different Fedora CoreOS (FCOS) update streams available.

        STABLE is the most reliable as changes only reach this stream once they
        spent time in testing.

        TESTING represents the next stable.

        NEXT is the the future and has the newest features before they filter
        down to the other streams.
        """
        STABLE = 'stable'
        TESTING = 'testing'
        NEXT = 'next'

    class Architecture(str, enum.Enum):
        AARCH64 = 'aarch64'
        PPC64LE = 'ppc64le'
        S390X = 's390x'
        X86_64 = 'x86_64'

        AMD64 = 'x86_64'  # Alias for X86-64. this is not what CoreOS calls it.


# At the time of writing there were four aarch64', 'ppc64le', 's390x', 'x86_64'
def default_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config['storage'] = {
        'images': 'storage/images',
    }

    return config

def write_default_config():
    config = default_config()
    with open('vm.ini', 'w') as writer:
        config.write(writer)


def check_cache(url: str, cache_directory: pathlib.Path):
    """Simple check to see if a URL has been fetched and was cached."""
    url_hash = hashlib.sha512(url.encode('utf-8'))
    request_directory = cache_directory / url_hash.hexdigest()
    etag_file = request_directory / 'etag.txt'
    response = request_directory / 'response'
    if etag_file.is_file() and response.is_file():
        return etag_file.read_text(), json.loads(response.read_text())
    return None, None


def handle_request_cache(response: requests.Response,
                         cache_directory: pathlib.Path):

    # If this needs to get too complicated consider:
    #   https://pypi.org/project/requests-cache/

    url_hash = hashlib.sha512(response.url.encode('utf-8'))
    request_directory = cache_directory / url_hash.hexdigest()
    request_directory.mkdir(exist_ok=True)

    # This would be better with sqlite rather than using two files for each
    # request.
    etag_file = request_directory / 'etag.txt'
    etag_file.write_text(response.headers['ETag'])

    response_file = request_directory / 'response'
    response_file.write_bytes(response.content)



def _fetch_json(url, cache_directory: pathlib.Path):
    """Fetch JSON from URL and use a cache if possible.."""
    etag, response_json = check_cache(url, cache_directory)

    if etag and ALWAYS_USE_CACHE:
        # Skip the conditional request.
        return response_json
    if etag:
        response = requests.get(url,
                                headers={
                                    'If-None-Match': etag,
                                })
        response.raise_for_status()
        if response.status_code == 304:
            # Content was not modified, don't need to request the whole thing.
            assert not response.content
        else:
            # Assume there was a change.
            #
            # Cache the updated response.
            handle_request_cache(response, cache_directory)
            return response.json()
    else:
        response = requests.get(url)
        response.raise_for_status()
        handle_request_cache(response, cache_directory)
        return response.json()


def download_file(url, output_location: pathlib.Path, output_filename: str):
    # Source: https://stackoverflow.com/a/16696317
    output_location.mkdir(exist_ok=True)
    output_path = output_location / output_filename
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk:
                f.write(chunk)
    return output_path


def hash_file_sha256(source_file: pathlib.Path):
    sha256 = hashlib.sha256()
    with open(source_file, 'rb') as reader:
        while True:
            data = reader.read(16 * 1024 * 1024)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def fetch_coreos(storage_directory,
                 provider: str = 'hyperv',
                 architecture: CoreOS.Architecture = CoreOS.Architecture.AMD64,
                 stream: CoreOS.Stream = CoreOS.Stream.STABLE):
    """Downloads CoreOS artifact.

    Artifact here means hard drive image however CoreOS system uses artifact
    for that to keep image meaning image on a cloud provider.

    Parameters
    ----------
    storage_directory
        The directory where the hard drive images will be downloaded.
    provider
        The virtualisation providers (software or cloud providers).
        Example are: aiyun, aws, azure, azurestack, digitalocean,
        exoscale, gcp, hyperv, ibmcloud, kubevirt, metal, nutanix, openstack,
        qemu, virtualbox, vmware, vultr.
    architecture
        The CPU architecture that that CoreOS will run on.
    stream
        The stream represents the how much how much testing and time has gone
        through on the results. The stable stream provides the most
        reliability.
    """
    storage_directory = pathlib.Path(storage_directory)

    url = f'https://builds.coreos.fedoraproject.org/streams/{stream.value}.json'

    cache_directory = pathlib.Path(CACHE_DIRECTORY)
    logging.info('Fetching CoreOS for %s on %s with stream %s',
                 provider, architecture.value, stream.value)
    stream_metadata = _fetch_json(url, cache_directory)
    #print(stream_metadata['architectures'].keys())

    # The stream metadata is:
    # - stream - a string that should match stream.value
    # - metadata.last-modified : a string with ISO-8061
    # - metadata.generator : a string
    # - architectures - object where keys are the architectures and the values
    #   are an object with artifacts and images.
    #
    # architectures[i].artifacts
    # architectures[i].images refer is an object for cloud providers where
    # the key is a cloud provider such as aws and gcp and the the values are
    # details about it including the name of the image in their system.
    arch_metadata = stream_metadata['architectures'][architecture.value]
    formats = arch_metadata['artifacts'][provider]['formats']

    # The provider metadata has the following:
    # - release - a string of the version number
    # - formats - a objects where the keys are the format and values is
    #   another object (let call it the format object)
    # - formats[format].disk.location -a string with the URL to the download
    #    location.
    # - formats[format].disk.signature -a string with the URL to the download
    #   signature file.
    # - formats[format].disk.sha256 -a string containing the SHA256 of the file
    #    in location.
    # - formats[format].disk.uncompressed-sha256 -a string containing the SHA256
    #    of the file in location after it is decompressed.

    # Editorial note: It is a shame it doesn't contain the file size.

    if provider == 'hyperv':
        # Options would be vhdx.zip, vhd.xz (used for azure).
        desired_format = 'vhdx.zip'
    elif len(formats) == 1:
        # There is only one format so assume that is what we want.
        desired_format = next(iter(formats.keys()))
    else:
        raise NotImplementedError('Not sure a default format for provider.')

    format_metadata = formats[desired_format]
    download_url = format_metadata["disk"]["location"]

    local_filename = download_url.split('/')[-1]

    if (storage_directory / local_filename).is_file():
        logging.info('Validating file %s', storage_directory / local_filename)
        actual_sha256 = hash_file_sha256(storage_directory / local_filename)
        expected_sha256 = format_metadata["disk"]["sha256"]
        if actual_sha256 == format_metadata["disk"]["sha256"]:
            logging.info('Existing file %s matches expected SHA-256 %s',
                         storage_directory / local_filename, expected_sha256)
        else:
            logging.error('Existing file %s did not match expected SHA-256 %s '
                          'as it was %s',
                          storage_directory / local_filename, expected_sha256,
                          actual_sha256)
            raise ValueError(
                f'Existing file {storage_directory / local_filename} did not '
                f'match expected SHA-256 {expected_sha256} as it was ' +
                actual_sha256
            )
    else:
        logging.info('Downloading %s to %s', download_url,
                     storage_directory / local_filename)
        download_file(download_url, storage_directory)


if __name__ == '__main__':
    if not os.path.isfile('vm.ini'):
        write_default_config()

    config = configparser.ConfigParser()
    config.read('vm.ini')

    logging.basicConfig(level=logging.DEBUG)
    CACHE_DIRECTORY = config['storage'].get('cache', CACHE_DIRECTORY)
    fetch_coreos(config['storage']['images'])
