
import datetime

from mediafeed import emls, NAMESPACES


		# <ns2:EventIdentifier Id="29581">
		# 	<ns2:EventName>2023 Referendum</ns2:EventName>
		# </ns2:EventIdentifier>

def event(root):
    # eml:ElectionIdentifier
    event_name = root.find('./mf:Results/eml:EventIdentifier/eml:EventName',
                           NAMESPACES)
    return event_name.text


def election_id(election_parent):
    """election_parent must be a XML element with an Election node.

    For the referendum, the Election node was a Media Feed Election rather than
    an EML Election.
    """
    election_id = election_parent.find('./mf:Election/eml:ElectionIdentifier',
                                       NAMESPACES)
    election_name = election_id.find('./eml:ElectionName', NAMESPACES).text
    election_cat = election_id.find('./eml:ElectionCategory', NAMESPACES).text
    return {
        'ElectionName': election_name,
        'ElectionCategory': election_cat,
    }


def phase(root):
    return root.find('./mf:Results', NAMESPACES).attrib["Phase"]


def _decode_option(option_xml):
    votes = option_xml.find('./mf:Votes', NAMESPACES)
    option_id = option_xml.find('./eml:ReferendumOptionIdentifier',
                                NAMESPACES)

    # There is a breakdown of the votes by type.
    # - Ordinary, Absent, Provisional, PrePoll and Postal.

    return {
        'ID': option_id.attrib['Id'],
        'Value': option_id.text,
        'Total Vote (%)': float(votes.attrib['Percentage']),
        'Total Vote': int(votes.text),
        }


def by_district(root):
    """Breakdown the results by district.

    This could break down each district result by polling place as well.
    It could show formal, informal and total.
    """
    path = './mf:Results/mf:Election/mf:Referendum/mf:Contests/mf:Contest/'
    path += 'mf:PollingDistricts/mf:PollingDistrict'
    for selection in root.findall(path, NAMESPACES):
        district_id = selection.find('./mf:PollingDistrictIdentifier',
                                     NAMESPACES)
        enrolment = selection.find('./mf:Enrolment', NAMESPACES)

        results = selection.find('./mf:ProposalResults', NAMESPACES)

        # Results come in couple of flavours: Option, Formal, Informal and
        # Total where Option has the yes and no counts.

        options = [
            _decode_option(option_xml)
            for option_xml in results.findall('./mf:Option', NAMESPACES)
        ]

        yield {
            'District Code': district_id.attrib['ShortCode'],
            'Name': district_id.find('./mf:Name', NAMESPACES).text,
            'State': district_id.find('./mf:StateIdentifier',
                                      NAMESPACES).attrib['Id'],
            'Enrolled': int(enrolment.attrib['CloseOfRolls']),
            'Historic Enrolled': int(enrolment.attrib['Historic']),
            'Polling Places': {
                'Returned': int(results.attrib['PollingPlacesReturned']),
                'Expected': int(results.attrib['PollingPlacesExpected']),
            },
            'Options': options,
        }


def by_states(root):
    """Breakdown the results by state."""
    path = './mf:Results/mf:Election/mf:Referendum/mf:Analysis/mf:States/'
    path += 'mf:State'

    for selection in root.findall(path, NAMESPACES):
        state_id = selection.find('./mf:StateIdentifier',
                                  NAMESPACES).attrib['Id']
        enrolment = selection.find('./mf:Enrolment', NAMESPACES)

        options = [
            _decode_option(option_xml)
            for option_xml in selection.findall(
                './mf:ProposalResults/mf:Option',
                NAMESPACES)
        ]

        yield {
            'State': state_id,
            'Enrolled': int(enrolment.attrib['CloseOfRolls']),
            'Historic Enrolled': int(enrolment.attrib['Historic']),
            'Options': options,
        }


def print_by_district(eml):
    for district in by_district(eml):
        print(district['Name'] + ' - ' + district['State'])
        option_summary = '\n'.join(
            f"  {option['Value']:3s} {option['Total Vote']}"
            for option in district['Options']
        )
        print(option_summary)
        break

def print_by_states(eml):
    for state in by_states(eml):
        # print('Possible ', state['Enrolled'], ' historically ',
        #       state['Historic Enrolled'])
        option_summary = ', '.join(
            f"{option['Value']} {option['Total Vote']}"
            for option in state['Options']
        )
        print('%3s' % state['State'] + " - " + option_summary)


if __name__ == '__main__':
    EMLS_29581 = r'D:\Downloads\AEC-2023-Referendum\29581-Detailed\Verbose'

    # This script is intended to be able to replay the time as it happens,
    # rather than collect up all the results and convert them to a NetCDF or
    # Xarray.

    for eml in emls(EMLS_29581):
        #print(event(eml))
        #print(election_id(eml.find('./mf:Results', NAMESPACES)))
        created = eml.find('./mf:Cycle', NAMESPACES).attrib['Created']

        print(phase(eml), datetime.datetime.fromisoformat(created))

        #print_by_district(eml)
        #print_by_states(eml)