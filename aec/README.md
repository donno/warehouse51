AEC
---
Various scripts for working with data from the AEC (Australian Electoral
Commission).

The main module is `mediafeed`, which provides functions for working with data
from the [media feed][1].

Supplementary modules/scripts:

* preload - Process pre-load data from the AEC . This is data typically offered
  at the before the first votes are counted such that media companies can load
  it into their systems. that media companies can load it into their systems.
* referendum - Helps with working with media feed data for the 2023 Referendum
  in Australia. This did not quite use the standard EML (Election Markup
  Language).
* geometry - At this stage mainly provides a module for [downloading][2] the
  shapefiles for the electoral divisions of each state and territory.

[1]: https://www.aec.gov.au/media/mediafeed/index.htm
[2]: https://www.aec.gov.au/Electorates/gis/gis_datadownload.htm
