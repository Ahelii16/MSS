# -*- coding: utf-8 -*-
"""

    mslib.mswms.mpl_hsec
    ~~~~~~~~~~~~~~~~~~~~

    Horizontal section style super classes for use with the
    HorizontalSectionDriver class.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
# style definitions should be put in mpl_hsec_styles.py

from __future__ import division


from future import standard_library
standard_library.install_aliases()


import io
import logging
from abc import abstractmethod
import mss_wms_settings

import matplotlib as mpl
import numpy as np
import PIL.Image
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from mslib.mswms import mss_2D_sections
from mslib.utils import get_projection_params


BASEMAP_CACHE = {}
BASEMAP_REQUESTS = []


class AbstractHorizontalSectionStyle(mss_2D_sections.Abstract2DSectionStyle):
    """Abstract horizontal section super class. Use this class as a parent
       to classes implementing different plotting backends. For example,
       to derive a Matplotlib-based style class, or a Magics++-based
       style class.
    """

    @abstractmethod
    def plot_hsection(self):
        """Re-implement this function to perform the actual plotting.
        """
        pass


class MPLBasemapHorizontalSectionStyle(AbstractHorizontalSectionStyle):
    """Matplotlib-based super class for all horizontal section styles.
       Sets up the map projection and draws a basemap.
    """
    name = "BASEMAP"
    title = "Matplotlib basemap"

    def _plot_style(self):
        """Overwrite this method to plot style-specific data on the map.
        """
        pass

    def supported_epsg_codes(self):
        return list(mss_wms_settings.epsg_to_mpl_basemap_table.keys())

    def support_epsg_code(self, crs):
        """Returns a list of supported EPSG codes.
        """
        try:
            get_projection_params(crs)
        except ValueError:
            return False
        return True

    def supported_crs(self):
        """Returns a list of the coordinate reference systems supported by
           this style.
        """
        crs_list = set([
            "EPSG:3031",  # WGS 84 / Antarctic Polar Stereographic
            "EPSG:3995",  # WGS 84 / Arctic Polar Stereographic
            "EPSG:3857",  # WGS 84 / Spherical Mercator
            "EPSG:4326",  # WGS 84 / cylindric
            "MSS:stere"])
        for code in self.supported_epsg_codes():
            crs_list.add("EPSG:{:d}".format(code))
        return sorted(crs_list)

    def _draw_auto_graticule(self, bm):
        """
        """
        # Compute some map coordinates that are required below for the automatic
        # determination of which meridians and parallels to draw.
        axis = bm.ax.axis()
        upperLeftCornerLon, upperLeftCornerLat = bm(axis[0], axis[3], inverse=True)
        lowerRightCornerLon, lowerRightCornerLat = bm(axis[1], axis[2], inverse=True)
        middleUpperBoundaryLon, middleUpperBoundaryLat = bm(np.mean([axis[0], axis[1]]), axis[3], inverse=True)
        middleLowerBoundaryLon, middleLowerBoundaryLat = bm(np.mean([axis[0], axis[1]]), axis[2], inverse=True)

        # Determine which parallels and meridians should be drawn.
        #   a) determine which are the minimum and maximum visible
        #      longitudes and latitudes, respectively. These
        #      values depend on the map projection.
        if bm.projection in ['npstere', 'spstere', 'stere', 'lcc']:
            # For stereographic projections: Draw meridians from the minimum
            # longitude contained in the map at one of the four corners to the
            # maximum longitude at one of these corner points. If
            # the map centre is contained in the map, draw all meridians
            # around the globe.
            # FIXME? This is only correct for polar stereographic projections.
            # Draw parallels from the min latitude contained in the map at
            # one of the four corners OR the middle top or bottom to the
            # maximum latitude at one of these six points.
            # If the map centre in contained in the map, replace either
            # start or end latitude by the centre latitude (whichever is
            # smaller/larger).

            # check if centre point of projection is contained in the map,
            # use projection coordinates for this test
            centre_x = bm.projparams["x_0"]
            centre_y = bm.projparams["y_0"]
            contains_centre = (centre_x < bm.urcrnrx) and (centre_y < bm.urcrnry)
            # merdidians
            if contains_centre:
                mapLonStart = -180.
                mapLonStop = 180.
            else:
                mapLonStart = min(upperLeftCornerLon, bm.llcrnrlon,
                                  bm.urcrnrlon, lowerRightCornerLon)
                mapLonStop = max(upperLeftCornerLon, bm.llcrnrlon,
                                 bm.urcrnrlon, lowerRightCornerLon)
            # parallels
            mapLatStart = min(middleLowerBoundaryLat, lowerRightCornerLat,
                              bm.llcrnrlat,
                              middleUpperBoundaryLat, upperLeftCornerLat,
                              bm.urcrnrlat)
            mapLatStop = max(middleLowerBoundaryLat, lowerRightCornerLat,
                             bm.llcrnrlat,
                             middleUpperBoundaryLat, upperLeftCornerLat,
                             bm.urcrnrlat)
            if contains_centre:
                centre_lat = bm.projparams["lat_0"]
                mapLatStart = min(mapLatStart, centre_lat)
                mapLatStop = max(mapLatStop, centre_lat)
        else:
            # for other projections (preliminary): difference between the
            # lower left and the upper right corner.
            mapLonStart = bm.llcrnrlon
            mapLonStop = bm.urcrnrlon
            mapLatStart = bm.llcrnrlat
            mapLatStop = bm.urcrnrlat

        # b) parallels and meridians can be drawn with a spacing of
        #      >spacingValues< degrees. Determine the appropriate
        #      spacing for the lon/lat differences: about 10 lines
        #      should be drawn in each direction. (The following lines
        #      filter the spacingValues list for all spacing values
        #      that are larger than lat/lon difference / 10, then
        #      take the first value (first values that's larger)).
        spacingValues = [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 40]
        deltaLon = mapLonStop - mapLonStart
        deltaLat = mapLatStop - mapLatStart
        spacingLon = [i for i in spacingValues if i > (deltaLon / 10.)][0]
        spacingLat = [i for i in spacingValues if i > (deltaLat / 10.)][0]

        #   c) parallels and meridians start at the first value in the
        #      spacingLon/Lat grid that's smaller than the lon/lat of the
        #      lower left corner; they stop at the first values in the
        #      grid that's larger than the lon/lat of the upper right corner.
        lonStart = np.floor((mapLonStart / spacingLon)) * spacingLon
        lonStop = np.ceil((mapLonStop / spacingLon)) * spacingLon
        latStart = np.floor((mapLatStart / spacingLat)) * spacingLat
        latStop = np.ceil((mapLatStop / spacingLat)) * spacingLat

        #   d) call the basemap methods to draw the lines in the determined
        #      range.
        bm.map_parallels = bm.drawparallels(np.arange(latStart, latStop,
                                                      spacingLat),
                                            labels=[1, 1, 0, 0],
                                            color='0.5', dashes=[5, 5])
        bm.map_meridians = bm.drawmeridians(np.arange(lonStart, lonStop,
                                                      spacingLon),
                                            labels=[0, 0, 0, 1],
                                            color='0.5', dashes=[5, 5])

    def plot_hsection(self, data, lats, lons, bbox=(-180, -90, 180, 90),
                      level=None, figsize=(960, 640), crs=None,
                      proj_params=None,
                      valid_time=None, init_time=None, style=None,
                      resolution=-1, noframe=False, show=False,
                      transparent=False):
        logging.debug("plotting data..")

        # Copy parameters to properties.
        self.data = data
        self.data_units = self.driver.data_units.copy()
        self.lats = lats
        self.lons = lons
        self.level = level
        self.valid_time = valid_time
        self.init_time = init_time
        self.style = style
        self.resolution = resolution
        self.noframe = noframe
        self.crs = crs

        # Derive additional data fields and make the plot.
        logging.debug("preparing additional data fields..")
        self._prepare_datafields()

        logging.debug("creating figure..")
        dpi = 80
        figsize = (figsize[0] / dpi), (figsize[1] / dpi)
        facecolor = "white"
        fig = plt.figure(figsize=figsize, dpi=dpi, facecolor=facecolor)
        logging.debug("\twith frame and legends" if not noframe else
                      "\twithout frame")

        ax = plt.axes([0.0, 0.0, 1.0, 1.0], projection=ccrs.Robinson())

        # Return the image as png embedded in a StringIO stream.
        # canvas = FigureCanvas(fig)
        output = io.BytesIO()
        plt.savefig(output, bbox_inches='tight')

        if show:
            logging.debug("saving figure to mpl_hsec.png ..")
            plt.savefig("mpl_hsec.png", bbox_inches='tight')

        # Convert the image to an 8bit palette image with a significantly
        # smaller file size (~factor 4, from RGBA to one 8bit value, plus the
        # space to store the palette colours).
        # NOTE: PIL at the current time can only create an adaptive palette for
        # RGB images, hence alpha values are lost here. If transpareny is
        # requested, the figure face colour is stored as the "transparent"
        # colour in the image. This works in most cases, but might lead to
        # visible artefacts in some cases.
        logging.debug("converting image to indexed palette.")
        # Read the above stored png into a PIL image and create an adaptive
        # colour palette.
        output.seek(0)  # necessary for PIL.Image.open()
        palette_img = PIL.Image.open(output).convert(mode="RGB").convert("P", palette=PIL.Image.ADAPTIVE)
        output = io.BytesIO()
        if not transparent:
            logging.debug("saving figure as non-transparent PNG.")
            palette_img.save(output, format="PNG")  # using optimize=True doesn't change much
        else:
            # If the image has a transparent background, we need to find the
            # index of the background colour in the palette. See the
            # documentation for PIL's ImagePalette module
            # (http://www.pythonware.com/library/pil/handbook/imagepalette.htm). The
            # idea is to create a 256 pixel image with the same colour palette
            # as the original image and use it as a lookup-table. Converting the
            # lut image back to RGB gives us a list of all colours in the
            # palette. (Why doesn't PIL provide a method to directly access the
            # colours in a palette??)
            lut = palette_img.resize((256, 1))
            lut.putdata(list(range(256)))
            lut = [c[1] for c in lut.convert("RGB").getcolors()]
            facecolor_rgb = list(mpl.colors.hex2color(mpl.colors.cnames[facecolor]))
            for i in [0, 1, 2]:
                facecolor_rgb[i] = int(facecolor_rgb[i] * 255)
            facecolor_index = lut.index(tuple(facecolor_rgb))

            logging.debug(u"saving figure as transparent PNG with transparency index %s.", facecolor_index)
            palette_img.save(output, format="PNG", transparency=facecolor_index)

        logging.debug("returning figure..")
        return output.getvalue()

    def shift_data(self):
        """Shift the data fields such that the longitudes are in the range
        left_longitude .. left_longitude+360, where left_longitude is the
        leftmost longitude appearing in the plot.

        Necessary to prevent data cut-offs in situations where the requested
        map covers a domain that crosses the data longitude boundaries
        (e.g. data is stored on a -180..180 grid, but a map in the range
        -200..-100 is requested).
        """
        # Determine the leftmost longitude in the plot.
        axis = self.bm.ax.axis()
        ulcrnrlon, ulcrnrlat = self.bm(axis[0], axis[3], inverse=True)
        left_longitude = min(self.bm.llcrnrlon, ulcrnrlon)
        logging.debug(u"shifting data grid to leftmost longitude in map %2.f..", left_longitude)

        # Shift the longitude field such that the data is in the range
        # left_longitude .. left_longitude+360.
        self.lons = ((self.lons - left_longitude) % 360) + left_longitude
        lon_indices = self.lons.argsort()
        self.lons = self.lons[lon_indices]

        # Shift data fields correspondingly.
        for key in self.data:
            self.data[key] = self.data[key][:, lon_indices]

    def mask_data(self):
        """Mask data arrays so that all values outside the map domain
           are masked. This is required for clabel to work correctly.

        See:
        http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg02892.html
        (Re: [Matplotlib-users] clabel and basemap).

        (mr, 2011-01-18)
        """
        # compute native map projection coordinates of lat/lon grid.
        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        x, y = self.bm(lonmesh_, latmesh_)
        # test which coordinates are outside the map domain.

        add_x = ((self.bm.xmax - self.bm.xmin) / 10.)
        add_y = ((self.bm.ymax - self.bm.ymin) / 10.)

        mask1 = x < self.bm.xmin - add_x
        mask2 = x > self.bm.xmax + add_x
        mask3 = y > self.bm.ymax + add_y
        mask4 = y < self.bm.ymin - add_y
        mask = mask1 + mask2 + mask3 + mask4
        # mask data arrays.
        for key in self.data:
            self.data[key] = np.ma.masked_array(
                self.data[key], mask=mask, keep_mask=False)
