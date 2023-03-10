"""Provides the ability to work with ABN bulk extract.

See:
https://data.gov.au/dataset/ds-dga-5bd7fcab-e315-42cb-8daf-50b7efc2027e/

For details see: bulkextract.xsd

TODO:
    Utilise the metadata() function to provide a download command.
"""

import argparse
import json
import urllib.request

from lxml import etree

DATASET_ID = '5bd7fcab-e315-42cb-8daf-50b7efc2027e'


def metadata():
    """Request the metadata for the dataset that this operates on.

    Returns
    -------
    dict
        A dictionary containing the metadata for the dataset.
        The format is dictated by CKAN (https://docs.ckan.org/en/2.10/).
        The main information is under the 'result' item.

    Raises
    ------
    urllib.error.HTTPError
        If there is a problem communicating with the server that has the
        metadata about the package.
    ValueError
        If the HTTP request was successful but the payload indicated a problem.
    """
    uri = f'https://data.gov.au/data/api/3/action/package_show?id={DATASET_ID}'

    # The documentation for this request is at:
    # https://data.gov.au/data/api/3/action/help_show?name=package_show

    # The use of urllib is deliberate at this stage as I didn't want to depend
    # on requests for such a tiny thing.
    response = urllib.request.urlopen(uri)
    metadata = json.load(response)
    if not metadata['success']:
        raise ValueError('Unsuccessful at retrieving dataset metadata.')
    return metadata['result']


def parse(path):
    """Parse data from the ABN bulk textract

    Data Metadata
    -------------
    Title: ABN Bulk Extract
    Licence: Creative Commons Attribution 3.0 Australia
    Publisher: Australian Business Register
    Jurisdiction: Commonwealth of Australia
    Source: https://data.gov.au/data/dataset/abn-bulk-extract
    """
    tree = etree.parse(path)
    return tree.xpath('/Transfer/ABR')


def sole_traders(data):
    """Limit the results for businesses that refer to sole traders."""

    def name(record):
        # IndividualName has elements: GivenName, FamilyName
        # Potential: NameTitleType

        name_element = record.xpath('./LegalEntity/IndividualName')[0]
        return ' '.join(element.text for element in name_element.getchildren())

    # NameTypeEnum (string type) with possible values:
    # MN, DGR, LGL, TRD, OTN and BN.
    for record in data:
        entity_type = record.xpath('./EntityType/EntityTypeInd')[0].text

        if entity_type == 'IND':
            yield name(record), record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Report information from the ABN bulk extract dataset.')
    parser.add_argument(
        'path', nargs='+',
        help='The path to the XML file for the dataset',
        # As of 2023, the dataset is broken down into multiple XML files
        # across two zips. With that in mind need to consider making this
        # accept a directory instead.
    )

    arguments = parser.parse_args()

    # The default behaviour is to print the names of sole traders as that is
    # all I've written so-far.
    for path in arguments.path:
        for name, details in sole_traders(parse(path)):
            print(name)

