"""
Explore the Registry of Open Data on AWS (RODA)

https://registry.opendata.aws/
"""

import json
import pathlib
import typing
import urllib.request

REGISTRY_NDJSON_URL = "https://registry.opendata.aws/index.ndjson"
REGISTRY_CHECKSUM_URL = "https://registry.opendata.aws/index.ndjson.sha256"


class Resource(typing.TypedDict):
    Description: str
    """A technical description of the data available within the AWS resource,
    including information about file formats and scope.
    """
    ARN: str
    """Amazon Resource Name for resource.

    Example: arn:aws:s3:::commoncrawl
    """
    Region: str
    """AWS region unique identifier.

    Example: us-east-1
    """
    Type: str
    """
    Can be CloudFront Distribution, DB Snapshot, S3 Bucket, or SNS Topic.

    A list of supported types is maintained at
    https://github.com/awslabs/open-data-registry/blob/main/resources.yaml
    """


class Entry(typing.TypedDict):
    # https://github.com/awslabs/open-data-registry

    Deprecated: bool
    Name: str
    """The public facing name of the dataset.

    Spell out acronyms and abbreviations.

    AWS do not require "AWS" or "Open Data" to be in the dataset name.
    Must be between 5 and 130 characters.
    """
    Description: str
    Documentation: str
    """A link to documentation of the dataset.

    Preferably hosted on the data provider's website or Github repository.
    """
    Sources: list[str]
    Contact: str
    """May be an email address, a link to contact form, a link to GitHub
    issues page, or any other instructions to contact the producer of the
    dataset
    """
    ManagedBy: str
    """The name of the laboratory, institution, or organization who is
    responsible for the data ingest process.

    Avoid using individuals. If your institution manages several datasets
    hosted by the Public Dataset Program, please list the managing institution
    identically.
    """
    UpdateFrequency: str
    """An explanation of how frequently the dataset is updated."""
    Tags: list[str]
    """Select tags that are related to an intrinsic property or descriptor of
    the dataset.

    A list of supported tags is maintained at
    https://github.com/awslabs/open-data-registry/blob/main/tags.yaml
    """
    License: str
    """An explanation of the dataset license and/or a URL to more information
    about data terms of use of the dataset
    """
    Resources: list[Resource]
    """A list of AWS resources that users can use to consume the data.
    """
    DataAtWork: dict  # TODO: Document
    RegistryEntryAdded: str
    """yyyy-mm-dd"""
    RegistryEntryLastModified: str
    """yyyy-mm-dd"""
    Slug: str


def cache_index() -> list[Entry]:
    """Cache the index file."""
    cache_directory = pathlib.Path.home() / ".local" / ".share"
    cache_file = cache_directory / "roda.ndjson"
    if not cache_file.is_file():
        cache_directory.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(REGISTRY_NDJSON_URL, cache_file)

    index = []
    with cache_file.open("r", encoding="utf-8") as reader:
        for line in reader:
            index.append(json.loads(line))

    return index


def main():
    index = cache_index()
    for item in index:
        for k, v in item.items():
            print(k, v)
        break


if __name__ == "__main__":
    main()
