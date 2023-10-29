"""Process pre-load data from the AEC (Australian Electoral Commission).

This is data typically offered at the before the first votes are counted such
that media companies can load it into their systems.

The intention is they load static election information, for example the
candidates names before election.

The first preload feed will be available a week after the close of nominations
and updated in the week before the election.
"""

import collections
import types
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
    def affiliation(self):
        """The affiliation of the candidate otherwise None.

        The affiliation has a name, short_code, id and affiliation type.
        """
        affiliation_id = self.xml.find(
            './eml:Affiliation/eml:AffiliationIdentifier',
            NAMESPACES)
        if not affiliation_id:
            # Most the times no affiliation means the candidate is
            # independent however this is not always the case.
            #assert self.independent, self.name
            return None

        return types.SimpleNamespace(
            name=affiliation_id.find('./eml:RegisteredName', NAMESPACES).text,
            short_code=affiliation_id.attrib['ShortCode'],
            id=affiliation_id.attrib['Id'],
            affiliation_type=self.xml.find('./eml:Affiliation/eml:Type',
                                           NAMESPACES).text,
        )

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


def load_candidates(path, *, election_category=None):
    """Loads the list of candidates for each election for the event.

    For example, the event may be the 2019 Federal Election, and the two
    elections taking place are:
    - House of Representatives Election
    - Senate Election

    The candidates are broken down by:
    - Election (Senate or House)
        - Contest (State or Electoral Division)

    If election_category is not None then only the candidates in the given
    election category will be included.
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
        election_as_dict = _election(election)

        if (election_category and
            election_as_dict['category'] != election_category):
            continue

        contests = election.findall('./eml:Contest', NAMESPACES)
        for contest in contests:
            # print(_contest(contest))

            actual_candidates = [
                Candidate(candidate)
                for candidate in contest.findall('./eml:Candidate', NAMESPACES)
            ]

            for c in actual_candidates:
                yield election_as_dict, _contest(contest), c



def report_professions():
    """Report on the different professions of each candidate."""
    profession_counter = collections.Counter(
        candidate.profession
        for _, _, candidate in load_candidates(PATH)
        if candidate.profession
    )

    print('Top 20 professions of candidates')
    for k, v in profession_counter.most_common(20):
        print(v, k)


def report_email_domains():
    """Report on the different email domains of each candidate.

    This is not available for the 2022 election as emails are not included in
    the preload data.
    """
    def _domain(email: str):
        return email.partition('@')[2]

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


def report_affiliations():
    """Report on the affiliations of each candidate."""
    def _domain(email: str):
        return email.partition('@')[2]

    affiliation_counter = collections.Counter(
        candidate.affiliation.name
        for _, _, candidate in load_candidates(PATH)
        if candidate.affiliation
    )

    if affiliation_counter:
        print('Top 20 affiliations (parties)')
        for k, v in affiliation_counter.most_common(20):
            print(v, k)
    else:
        print('No affiliations found.')


PATH = 'data/aec-mediafeed-Detailed-Preload-24310-20190515152735.zip'
PATH = 'data/aec-mediafeed-Detailed-Preload-27966-20220518111207.zip'


if __name__ == '__main__':
    # report_email_domains()
    # report_professions()
    report_affiliations()