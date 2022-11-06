"""Process pre-load data from the AEC (Australian Electoral Commission).

This is data typically offered at the before the first votes are counted such
that media companies can load it into their systems.

The intention is they load static election information, for example the
candidates names before election.

The first preload feed will be available a week after the close of nominations
and updated in the week before the election.
"""

import collections
import zipfile

try:
    import defusedxml.ElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree


NAMESPACES = {
    'eml': 'urn:oasis:names:tc:evs:schema:eml',
    'xal': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0',
}


class Candidate:
    def __init__(self, xml_element):
        self.xml = xml_element

    @property
    def independent(self) -> bool:
        assert self.xml.attrib['Independent'] in {'yes', 'no'}
        return self.xml.attrib['Independent'] == 'yes'

    @property
    def name(self) -> str:
        """The name of the candidate from their candidate identifier.

        It is also possible to retrieve more detailed information in the format
        of OASIS CIQ extensible Name Language (xNL)
        """
        return self.xml.find('./eml:CandidateIdentifier/eml:CandidateName',
                             NAMESPACES).text

    @property
    def email(self):
        """The email of the candidate if they provided one."""
        email = self.xml.find('./eml:Contact/eml:Email', NAMESPACES)
        return None if email is None else email.text

    @property
    def profession(self):
        profession = self.xml.find('./eml:Profession', NAMESPACES)
        return None if profession is None else profession.text

    def __repr__(self):
        return f'Candidate("{self.name}")'


def load(path, name_fragment):
    if not zipfile.is_zipfile(path):
        raise ValueError(f'Expected a ZIP file at the given path ({path})')

    with zipfile.ZipFile(path) as archive:
        xmls = [name for name in archive.namelist()
                if name.startswith('xml/') and name.endswith('xml')]

        path = next(zip_path for zip_path in xmls if name_fragment in zip_path)
        with archive.open(path) as xml:
            return ElementTree.parse(xml).getroot()

        # ['xml/aec-mediafeed-pollingdistricts-24310.xml',
        #  'xml/aec-mediafeed-results-detailed-preload-24310.xml',
        #  'xml/eml-110-event-24310.xml',
        #  'xml/eml-230-candidates-24310.xml']


def load_candidates(path):
    """Loads the list of candidates for each election for the event.

    For example, the event may be the 2019 Federal Election, and the two
    elections taking place are:
    - House of Representatives Election
    - Senate Election

    The candidates are broken down by:
    - Election (Senate or House)
        - Contest (State or Electoral Division)
    """

    def _event(candidates):
        """Return the event information from the candidate list XML element."""
        event_id = candidates.find('./eml:EventIdentifier', NAMESPACES)
        return {
            'id': event_id.attrib['Id'],
            'name': event_id.find('./eml:EventName', NAMESPACES).text,
        }

    def _election(election):
        """Return the election information from an election XML element."""
        election_id = election.find('./eml:ElectionIdentifier', NAMESPACES)
        return {
            'id': election_id.attrib['Id'],
            'name': election_id.find('./eml:ElectionName', NAMESPACES).text,
            'category': election_id.find('./eml:ElectionCategory',
                                         NAMESPACES).text
        }

    def _contest(contest):
        """Return the contest information from an contest XML element."""
        contest_id = contest.find('./eml:ContestIdentifier', NAMESPACES)
        return {
            'id': contest_id.attrib['Id'],
            'short_code': contest_id.attrib.get('ShortCode', None),
            'name': contest_id.find('./eml:ContestName', NAMESPACES).text,
        }

    candidates = load(path, '-candidates-')
    candidates = candidates.find('./eml:CandidateList', NAMESPACES)

    event = _event(candidates)

    elections = candidates.findall('./eml:Election', NAMESPACES)

    for election in elections:
        # print('------')
        # print(_election(election))

        contests = election.findall('./eml:Contest', NAMESPACES)
        for contest in contests:
            # print(_contest(contest))

            actual_candidates = [
                Candidate(candidate)
                for candidate in contest.findall('./eml:Candidate', NAMESPACES)
            ]

            for c in actual_candidates:
                yield _election(election), _contest(contest), c


PATH = 'data/aec-mediafeed-Detailed-Preload-24310-20190515152735.zip'
PATH = 'data/aec-mediafeed-Detailed-Preload-27966-20220518111207.zip'


if __name__ == '__main__':
    # for election, contest, candidate in load_candidates(PATH):
    #     print(election, contest)
    #     print(candidate)

    def _domain(email: str):
        return email.partition('@')[2]

    email_domains = {}
    domain_counter = collections.Counter(
        _domain(candidate.email)
        for _, _, candidate in load_candidates(PATH)
        if candidate.email
        # and candidate.independent
    )

    if domain_counter:
        print('Top 20 used domains of candidates')
        for k, v in domain_counter.most_common(20):
            print(v, k)

    profession_counter = collections.Counter(
        candidate.profession
        for _, _, candidate in load_candidates(PATH)
        if candidate.profession
    )

    print('Top 20 professions of candidates')
    for k, v in profession_counter.most_common(20):
        print(v, k)
