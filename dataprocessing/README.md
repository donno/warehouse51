dataprocessing
==============

A place to store various scripts that have a limited purpose or use with a 
focus on tools for processing open data.

Generally, these scripts are for when I come across some data that looks 
interesting and I find some insight that would be interesting to gleam from
them.


australia.html
--------------
This is a playground using Leaflet for working with the ABS data.

It requires au-ste-boundaries.json which can be generated with the
abs_boundaries.py script which will download, extract and convert the ESRI
Shapefile to GeoJSON.

Known Limitations
- State boundaries end up quite large, about 80 megabytes. It could do with
  the option to simplify them.

An alternative to consider is using plotly to create the maps straight from
Python. See https://plotly.com/python/choropleth-maps/
