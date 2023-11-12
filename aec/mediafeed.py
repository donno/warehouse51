"""Process data from the AEC (Australian Electoral Commission) Media Feed.

Not included:
- Handling for live elections where data is updated every 2-5 minutes.


EML Format
    See: https://docs.oasis-open.org/election/eml/v5.0/os/EML-Schema-Descriptions-v5.0.html

<EML>
    TransactionId
    Count
        EventIdentifier
            EventName
        Election
            ElectionIdentifier
            Contests
                Contest (0 or more)
</EML>

EventIdentifier
    Attribute: Id
        Example: 24310
EventName
    Example: 2019 Federal Election

ElectionIdentifier
    Attribute: Id
        Example: 24310
    Element: ElectionName
        Example: House of Representatives Election
    Element: ElectionCategory
        Example: House
"""

import dataclasses
import os
import zipfile
import pyarrow
import pyarrow.parquet

try:
    import defusedxml.ElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

ELECTIONS_ID_TO_NAME = {
    '24310', '2019 Federal Election',
}

ELECTION = 'V:\\24310_2019_Election\\Standard_Eml'

NAMESPACES = {
    'eml': 'urn:oasis:names:tc:evs:schema:eml',
    'mf': 'http://www.aec.gov.au/xml/schema/mediafeed',
}


@dataclasses.dataclass
class Affiliation:
    identifier: str
    short_code: str
    name: str

    @classmethod
    def from_xml(cls, xml):
        if xml.tag != f'{{{NAMESPACES["eml"]}}}AffiliationIdentifier':
            raise ValueError('Wrong XML element, expected '
                             '"AffiliationIdentifier"')

        name = xml.find('./eml:RegisteredName', NAMESPACES).text
        return cls(xml.attrib['Id'], xml.attrib['ShortCode'], name)


@dataclasses.dataclass
class Candidate:
    identifier: str
    name: str
    affiliation: Affiliation

    @classmethod
    def from_xml(cls, xml, affiliation):
        candidate_id = xml.find('./eml:CandidateIdentifier', NAMESPACES)
        name = candidate_id.find('./eml:CandidateName', NAMESPACES).text
        return cls(candidate_id.attrib['Id'], name, affiliation)


def eml_contests(eml):
    """Extracts the contest information from the EML."""
    needle = './eml:Count/eml:Election/eml:Contests/eml:Contest'
    for contest in eml.findall(needle, NAMESPACES):
        yield contest


def eml_contests_to_parquet(eml, contests, output_directory, minimised=False):
    """
    If minimised is True, then only the IDs for candidates and their
    affiliation are recorded.
    """

    # TODO: This only handles a single EML, to handle multiple it needs the
    # transaction ID added

    if minimised:
        raise NotADirectoryError('NYI')

    if contests is None:
        contests = eml_contests(eml)

    # Convert the data to arrays.
    contest_names = []
    candidate_names = []
    affiliation_names = []
    valid_votes = []

    for contest in contests:
        contest_id = contest.find('./eml:ContestIdentifier', NAMESPACES)
        # contest_id.attribs['Id'] and contest_id.attribs['ShortCode']
        contest_name = contest_id.find('./eml:ContestName', NAMESPACES).text

        for selection in contest.findall('./eml:TotalVotes/eml:Selection',
                                         NAMESPACES):
            affiliation_id = selection.find('./eml:AffiliationIdentifier',
                                            NAMESPACES)
            if affiliation_id:
                affiliation = Affiliation.from_xml(affiliation_id)
            else:
                affiliation = None

            candidate = Candidate.from_xml(
                selection.find('./eml:Candidate', NAMESPACES),
                affiliation)

            votes = int(selection.find('./eml:ValidVotes', NAMESPACES).text)

            # Populate the data.
            contest_names.append(contest_name)
            candidate_names.append(candidate.name)
            affiliation_names.append(affiliation.name if affiliation else '')
            valid_votes.append(votes)

    arrays = [contest_names, candidate_names, affiliation_names, valid_votes]

    event_id = eml.find('./eml:Count/eml:EventIdentifier', NAMESPACES)
    event_name = event_id.find('./eml:EventName', NAMESPACES).text

    election_id = eml.find('./eml:Count/eml:Election/eml:ElectionIdentifier',
                           NAMESPACES)
    election_name = election_id.find('./eml:ElectionName', NAMESPACES).text
    election_cat = election_id.find('./eml:ElectionCategory', NAMESPACES).text

    # Generally you each contest together.
    fields = [
        ('Contest', pyarrow.string()),
        ('Candidate', pyarrow.string()),
        ('Affiliation', pyarrow.string()),
        ('ValidVotes', pyarrow.int64()),  # Non-negative integer.
    ]

    # Create a schema
    schema = pyarrow.schema(
        fields,
        metadata={
            'EventIdentifierName': event_name,
            'EventIdentifierID': event_id.attrib['Id'],
            'ElectionIdentifierID': election_id.attrib['Id'],
            'ElectionName': election_name,
            'ElectionCategory': election_cat,
        },
    )

    # Write it out.
    writer = pyarrow.parquet.ParquetWriter(
        os.path.join(output_directory,
                     event_name.replace(' ', '_') + '.parquet'),
        schema)
    writer.write_table(pyarrow.table(arrays, schema=schema))
    writer.close()


def emls(directory):
    def _files():

        for file in os.scandir(directory):
            if all((file.name.startswith('aec-mediafeed-'),
                    # Australia's 2023 referendum didn't have this next one.
                    #'-Eml-' in file.name,
                    file.name.endswith('.zip'))):
                # Zipped
                yield True, file.path
            elif file.name.startswith('eml-') and file.name.endswith('.xml'):
                # Uncompressed
                yield False, file.path

    for compressed, path in _files():
        if compressed:
            with zipfile.ZipFile(path) as zipped_eml:
                xmls = [name for name in zipped_eml.namelist()
                        if name.startswith('xml/') and name.endswith('xml')]
                for name in xmls:
                    with zipped_eml.open(name) as eml:
                        yield ElementTree.parse(eml).getroot()

        else:
            with open(path) as eml:
                yield ElementTree.parse(eml).getroot()


if __name__ == '__main__':
    for eml in emls(ELECTION):
        # print(ElementTree.tostring(eml))
        eml_contests_to_parquet(eml, None, '')
        print(eml_contests(eml))
        break
