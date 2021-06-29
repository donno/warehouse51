tifftools
=========

Provides ability to to working with digital elevation models (DEM) stored in
TIFF files. If you are looking for a serious solution consider GDAL instead.

This is essentially a bespoke solution that is easy for me to play around
with and use without committing to using GDAL myself.

Authors
---------
 * Sean Donnellan <darkdonno@gmail.com>

License
---------------------
The MIT License (see LICENSE.txt)

Third Party Components
---------------------------
This depends on libtiff. In the future it could be made to optionally depend on
libgeotiff to avoid relying on my own tie-point look-up for GeoTIFF.
