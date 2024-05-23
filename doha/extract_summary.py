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
import logging
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


def extract_summary_from_pdf(path: pathlib.Path) -> Summary:
    """Extract the summary from PDF of an appeal board decision.

    This only works on older versions of the PDF which had the information.
    """
    pdftotext = pathlib.Path(r"D:\Programs\poppler\bin") / "pdftotext.exe"
    output = subprocess.check_output([str(pdftotext), str(path), "-"])
    lines = output.decode("utf-8").splitlines()
    return extract_summary(lines, path)


def extract_summary(lines: list[str], document_path: pathlib.Path) -> Summary:
    """Extract the summary from the given lines.

    Parameters
    ----------
    lines
        The lines containing the summary
    document_path
        THe path to the document that the summary is for. This is the PDF file.
    """
    # DKEYWORD appears in case 15-03162 in 2017.
    # `KEYWORD appears in case 19-02470.h1 in 2021.
    prefix, _, keywords = lines[0].partition(": ")
    if not prefix.startswith(("KEYWORD", "DKEYWORD", "`KEYWORD")):
        if len(lines) > 4 and any(
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
            error += f"for {document_path}"
            raise ValueError(error)

        error = f"Expected to find KEYWORD on first line in {document_path}"
        raise ValueError(error)

    if not lines[1].startswith("DIGEST:"):
        error = f"Expected to find DIGEST on second line in {document_path}"
        raise ValueError(error)

    # 2020 has the space, 2019 does not.and one from 2017 had the space between
    # the N and O.
    case_number_prefixes = ("CASE NO:", "CASENO:", "CASE N O: ", "CASE No.: ")

    end_digest = lambda line: not line.startswith(case_number_prefixes)
    digest = "\n".join(itertools.takewhile(end_digest, lines[1:]))
    digest = digest.partition(": ")[-1].strip()

    # This is the keep it simple version, the other idea was to simply iterate
    # over until we see each of the titles to support the multi-line DIGEST.

    # If there is no case number which happens in one of the txt file summaries
    # then default to using the name of the pdf which is typically named after
    # the case.
    case_number = next(
        (line for line in lines if line.startswith(case_number_prefixes)),
        f"CASE NO: {document_path.stem}",
    )

    case_number = case_number.partition(": ")[-1].strip()

    date_prefix = "DATE: "
    date = next(
        (
            line[len(date_prefix) :].strip()
            for line in lines
            if line.upper().startswith(date_prefix)
        ),
        None,
    )

    if date is None:
        error = f"Failed to parse date for {document_path}"
        raise ValueError(error)

    try:
        if "/" in date:
            if len(date) < 9:
                date = datetime.datetime.strptime(date, "%M/%d/%y")
            else:
                date = datetime.datetime.strptime(date, "%M/%d/%Y")
        else:
            date = datetime.datetime.strptime(date, "%B %d, %Y")
    except ValueError as orignal_error:
        error = f"Failed to parse date for {document_path}: {orignal_error}"
        raise ValueError(error) from None

    return Summary(
        document_path,
        keywords.split("; "),
        digest,
        case_number,
        date.date(),
    )


def extract_summaries(directory: pathlib.Path) -> None:
    """Extract the summaries of the appeal decision PDFs in directory."""
    pdfs = list(directory.glob("*.pdf"))
    for pdf in pdfs:
        # if pdf.name.endswith(('.a1.pdf', '.a2.pdf')):
        if pdf.name.endswith((".h1.pdf", ".h2.pdf", ".h3.pdf")):
            # These PDFS do not have the summary. They have a different form.
            #
            # However, for 2021 there may be a text file with the summary.
            text_summary = pdf.with_suffix(".txt")
            if text_summary.exists():
                # This could check that the file size is less than a megabyte
                # before loading it as a safe-guard.
                with text_summary.open() as reader:
                    lines = [
                        # Filter out lines that were blank, or nearly empty.
                        line.rstrip()
                        for line in reader
                        if not line.isspace()
                    ]

                summary = extract_summary(lines, pdf)
                yield summary
        else:
            try:
                summary = extract_summary_from_pdf(pdf)
                yield summary
            except ValueError:
                logging.warning("Failed to summarise: %s", pdf, exc_info=True)


def print_summaries(summaries):
    """Print out each of the given summaries."""
    for summary in summaries:
        print(summary)


def write_summaries_to_index(
    summaries, subtitle: str, index_path: pathlib.Path, *, generate_links: bool = False
):
    """Write out an index of the summaries to a file."""
    with index_path.open("w", encoding="utf-8") as writer:
        writer.write(f"# DOHA Appeal Board Decisions - {subtitle}")

        for summary in summaries:
            writer.write(f"## Case {summary.case_number}\n")
            writer.write("**Keywords**: " + "; ".join(summary.keywords) + "\\\n")
            writer.write(f"**Date**: {summary.date.isoformat()}\n")
            writer.write("\n")
            writer.write(summary.digest)
            if generate_links:
                relative_path = summary.document.relative_to(index_path.parent)
                writer.write(f"\n\n### [Read Report]({relative_path.as_posix()})\n")
            writer.write("\n\n")
    return index_path


def write_index_for_year(base_path: pathlib.Path, year: int, output_path: pathlib.Path):
    """Write out an index for the given year.

    The assumption is the documents for the given year are found in
    base_path / year.

    The output path should be a directory to write the file and it will be
    output_path / "doha_{year}.md".
    """
    generate_links = output_path.is_relative_to(base_path)
    summaries = extract_summaries(base_path / str(year))
    index_path = output_path / f"doha_{year}.md"
    return write_summaries_to_index(
        summaries,
        subtitle=str(year),
        index_path=index_path,
        generate_links=generate_links,
    )


if __name__ == "__main__":
    BASE_PATH = pathlib.Path(r"D:\Downloads\Documents\DOHA_Appeal_Board_Decisions")
    OUTPUT_PATH = pathlib.Path.cwd()
    WRITE_TO_FILE = True

    if WRITE_TO_FILE:
        write_index_for_year(BASE_PATH, 2017, OUTPUT_PATH)
        write_index_for_year(BASE_PATH, 2018, OUTPUT_PATH)
        write_index_for_year(BASE_PATH, 2019, OUTPUT_PATH)
        write_index_for_year(BASE_PATH, 2020, OUTPUT_PATH)
    else:
        print_summaries(extract_summaries(BASE_PATH / "2017"))
        print_summaries(extract_summaries(BASE_PATH / "2018"))
        print_summaries(extract_summaries(BASE_PATH / "2019"))
        # The 2021 data uses the text summaries which has a number of errors.
        #
        # Of which I went through each of them and fixed them up. For dates
        # cross checking them against the PDFs.
        print_summaries(extract_summaries(BASE_PATH / "2021"))
