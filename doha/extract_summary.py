"""Extract the summary from DOHA  appeal board decision.

This works for older PDFs of the decisions which started with keywords,
digest (summary), case number and date.

For example the 2020 claims from:
https://doha.ogc.osd.mil/CLAIMS-DIVISION/DOHA-Claims-Appeals-Board-Decisions/2020-DOHA-Claims-Appeals-Board-Decisions/
"""

from __future__ import annotations

import dataclasses
import datetime
import itertools
import pathlib
import subprocess

# from poppler import load_from_file
# The above library is needs to be built from source and doesn't have Windows
# support, in the end turns out calling out to pdftotext does what I want.


@dataclasses.dataclass
class Summary:
    """The summary of a appeal board decision document."""

    document: pathlib.Path
    keywords: list[str]
    digest: str
    case_number: str
    date: datetime.date


def extract_summary(path: pathlib.Path) -> Summary:
    """Extract the summary from PDF of an appeal board decision.

    This only works on older versions of the PDF which had the information.

    TITLES = ["KEYWORD: ", "DIGEST: ", "CASE NO: ", "DATE: "]
    """
    pdftotext = pathlib.Path(r"D:\Programs\poppler\bin") / "pdftotext.exe"
    output = subprocess.check_output([str(pdftotext), str(path), "-"])
    lines = output.decode("utf-8").splitlines()

    if any(
        [
            lines[0] == "DEPARTMENT OF DEFENSE",
            lines[2] == "DEPARTMENT OF DEFENSE",
            lines[4] == "DEPARTMENT OF DEFENSE",
        ],
    ):
        # It is possible to extract the date and ISCR Case number.
        case_number = next(
            line
            for line in lines
            if line.startswith(("ISCR Case No. ", "ADP Case No. "))
        )
        case_number = case_number.partition(". ")[-1]
        error = f"New format (Case {case_number}) - no summary is provided "
        error += f"for {path}"
        raise ValueError(error)

    # DKEYWORD appears in case 15-03162 in 2017.
    prefix, _, keywords = lines[0].partition(": ")
    if not prefix.startswith(("KEYWORD", "DKEYWORD")):
        error = f"Expected to find KEYWORD on first line in {path}"
        raise ValueError(error)

    if not lines[1].startswith("DIGEST:"):
        error = f"Expected to find DIGEST on second line in {path}"
        raise ValueError(error)

    # 2020 has the space, 2019 does not.and one from 2017 had the space between
    # the N and O.
    case_number_prefixes = ("CASE NO:", "CASENO:", "CASE N O: ", "CASE No.: ")

    end_digest = lambda line: not line.startswith(case_number_prefixes)
    digest = "\n".join(itertools.takewhile(end_digest, lines[1:]))
    digest = digest.partition(": ")[-1].strip()

    # This is the keep it simple version, the other idea was to simply iterate
    # over until we see each of the titles to support the multi-line DIGEST.
    case_number = next(line for line in lines if line.startswith(case_number_prefixes))
    case_number = case_number.partition(": ")[-1].strip()

    date_prefix = "DATE: "
    date = next(
        line[len(date_prefix):].strip() for line in lines
        if line.upper().startswith(date_prefix)
    )

    if "/" in date:
        if len(date) < 9:
            date = datetime.datetime.strptime(date, "%M/%d/%y")
        else:
            date = datetime.datetime.strptime(date, "%M/%d/%Y")
    else:
        date = datetime.datetime.strptime(date, "%B %d, %Y")
        # error = f"Unable to handle date: {date}"
        # raise NotImplementedError(error)

    return Summary(path, keywords.split("; "), digest, case_number, date.date())


def extract_summaries(directory: pathlib.Path) -> None:
    """Extract the summaries of the appeal decision PDFs in directory."""
    pdfs = list(directory.glob("*.pdf"))
    for pdf in pdfs:
        # if pdf.name.endswith(('.a1.pdf', '.a2.pdf')):
        if pdf.name.endswith((".h1.pdf", ".h2.pdf")):
            # These PDFS do not have the summary. They have a different form.
            # 
            # However, for 2021 there may be a text file with the summary.
            continue
        summary = extract_summary(pdf)
        print(summary)


if __name__ == "__main__":
    BASE_PATH = pathlib.Path(r"D:\Downloads\Documents\DOHA_Appeal_Board_Decisions")
    extract_summaries(BASE_PATH / "2017")
    extract_summaries(BASE_PATH / "2018")
    extract_summaries(BASE_PATH / "2019")
    extract_summaries(BASE_PATH / "2020")
    extract_summaries(BASE_PATH / "2021")
