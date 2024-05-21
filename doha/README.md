DOHA Tools
==========
Tools for working with information from the Defense Office of Hearings and
Appeals.

The main goal is the appeal board deciscsionlogs at:
https://doha.ogc.osd.mil/CLAIMS-DIVISION/DOHA-Claims-Appeals-Board-Decisions

Tools
-----
- extract_summary.py - Extracts the summary from the start of the PDF files
  of appeals up until 2020.


### extract_summary.py
The appeals from 2021 had a corresponding text file with the summary, which can
be used by this script. Several text files were manually fixed up as one was
missing the KEYWORD: and DIGEST: prefix and a few others had invalid dates.

Overall it seems the files ending in .h1.pdf and .h2.pdf are in a different
format and the ones with the right format end in .a1.pdf or .a2.pdf.

TODOs
-----
- Extend extract_summary.py to read the summary from corresponding text file
  if available.
