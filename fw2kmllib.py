"""
Library for Arpak @TheRocketryForum's Featherweight to KML Converter

Author(s): Arpak, Aeva

Changelog
---------

 - March 21st, 2024: Updated Arpak's code for use with a gui

"""

import csv
import operator
import datetime
import time
from random import randint
from xml.etree.ElementTree import ElementTree, Element, SubElement
from pathlib import Path
from os import path

FLIGHTPATH_PERCENT_OPAQUE = 75

class fw2kml():
    """
    fw2kml util class
    """

    def __init__(self):
        pass
        #tbh, we can probably make this class a function "convertFile" instead

    @staticmethod
    def create_style_elem(line_color, poly_color, style_id, linestyle_id, polystyle_id):
        elem_style = Element("Style", attrib={"id":f"{style_id}"})

        elem_linestyle = SubElement(elem_style, "LineStyle", attrib={"id":f"{linestyle_id}"})
        elem_line_color = SubElement(elem_linestyle, "color")
        elem_line_color.text = line_color
        elem_line_colormode = SubElement(elem_linestyle, "colorMode")
        elem_line_colormode.text = "normal"

        elem_polystyle = SubElement(elem_style, "PolyStyle", attrib={"id":f"{polystyle_id}"})
        elem_poly_color = SubElement(elem_polystyle, "color")
        elem_poly_color.text = poly_color
        elem_poly_color = SubElement(elem_polystyle, "colorMode")
        elem_poly_color.text = "normal"
        elem_fill = SubElement(elem_polystyle, "fill")
        elem_fill.text = "1"
        elem_outline = SubElement(elem_polystyle, "outline")
        elem_outline.text = "1"

        return elem_style

    @staticmethod
    def create_flight_plot(placemark_id, flight_id, style_id, linestring_id, coordinates):
        elem_mark = Element("Placemark", attrib={"id":f"{placemark_id}"})
        elem_name = SubElement(elem_mark, "name")
        elem_name.text=f"fw2kml - Flight {flight_id}"
        style_url = SubElement(elem_mark, "styleUrl")
        style_url.text=f"#{style_id}"

        elem_lenstr = SubElement(elem_mark, "LineString", attrib={"id":f"{linestring_id}"})
        extrude = SubElement(elem_lenstr, "extrude")
        extrude.text = "1"
        altmode = SubElement(elem_lenstr, "altitudeMode")
        altmode.text = "absolute"
        # TODO maybe make this iterate over a list instead
        coorlist = SubElement(elem_lenstr, "coordinates")
        coorlist.text = coordinates
        return elem_mark

    def convertFile(self, droppedFile):
        """
        convertFile(droppedFile)
        convert the contents of a file from FeatherWeightCSV to Google Maps KML
        droppedFile - (str) path to file to be converted
        """
        # instance variables
        # Number of detected flights, used for color coordination (currently uses time gaps)
        totalflights = 1
        badtimedata = False

        print(f"Processing file: {droppedFile}")

        # load csv into memory (top row becomes fields)
        rows = []
        fields = []
        with open(droppedFile, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            fields = next(csvreader)
            for row in csvreader:
                rows.append(row)

        if "LAT" not in fields or \
            "LON" not in fields or \
             "ALT" not in fields:
            print("Necessary fields for latitude, longitude, and altitude are missing. " +\
                    "Cannot process file.")
            return

        # Figure out which field is alt, lon, and lat
        latindex = fields.index("LAT")
        lonindex = fields.index("LON")
        altindex = fields.index("ALT")

        if "UNIXTIME" in fields:
            # Attempt to find UNIXTIME, first format given to me does not include this field.
            unixtimeindex = fields.index("UNIXTIME")

            rows = sorted(rows, key=operator.itemgetter(unixtimeindex))
        elif "TIME" in fields and "DATE" in fields:
            print("No unixtime field found, Looking for 'TIME'")
            timeindex = fields.index("TIME")
            dateindex = fields.index("DATE")

            # Convert DATE and TIME into UNIXTIME (will reuse the TIME field temporarily)
            for row in rows:
                # Format date and time into a usable string
                formatted_datetime = "{}_{}".format(row[dateindex], row[timeindex])
                # convert time field into unixtime   Example: 2022-11-05_10:43:00.789 to UNIXTIME
                row[timeindex] = time.mktime(datetime.datetime.strptime(\
                        formatted_datetime, "%Y-%m-%d_%H:%M:%S.%f").timetuple())

            unixtimeindex = fields.index("TIME")
            rows = sorted(rows, key=operator.itemgetter(unixtimeindex))
        else:
            print("Could not find TIME or DATE, will not sort for time jitter or split flights.")
            badtimedata = True

        # Determine the outputed file's name
        file_basename = ".".join(str(droppedFile).split(".")[:-1])
        new_ext = "_fw2kml.kml"
        num_converted = 0
        outfile_name = None
        while True:
            outfile_name = f"{file_basename}_{num_converted}{new_ext}"
            if not path.isfile(Path(outfile_name)):
                break
            num_converted += 1

        # Create list of coordinates that pass error check
        coords = []
        flightcoords = []
        last_time_unix = rows[1][unixtimeindex]   # instantiate last_time_unix to first timestamp
        for row in rows:
            if float(row[5]) <= 0:
                print("Bad data, skipping", row[5])
            else:
                # If 1 minute goes by, consider it a new flight - If theres badtimedata, just
                # let it dump everything into one coordstring
                if badtimedata or float(row[unixtimeindex])-float(last_time_unix) < 60:
                    coords.append("{},{},{}".format(row[lonindex], row[latindex], \
                            (int(row[altindex]) * 0.3048)))
                else:
                    print("New flight detected")
                    totalflights += 1
                    coordstring = ' '.join(coords)
                    flightcoords.append(coordstring)
                    coords = []

            last_time_unix = row[unixtimeindex]

        # Convert coordinate list into coordinate string with ' ' as delimiter
        coordstring = ' '.join(coords)
        flightcoords.append(coordstring)

        print(flightcoords)
        kml_tree = ElementTree()
        elem_kml = Element("kml", attrib={
                "xmlns":"http://www.opengis.net/kml/2.2",
                "xmlns:gx":"http://www.google.com/kml/ext/2.2"
            }
        )
        # pylint doesn't like this, and it seems to be unrecommended to do this
        kml_tree._setroot(elem_kml)

        # Note: I don't think attribute id is needed
        elem_doc = SubElement(elem_kml, "Document", attrib={"id":"1"})
        elem_name = SubElement(elem_doc, "Name", attrib={})
        elem_name.text = "fw2kml FeatherWeight KML"

        for flight_num in range(totalflights):
            # Super lazy way to generate random colors
            # basically doing randhex(0x0, 0xFFFFFF) but in decimal
            color = str(hex(randint(0,int(0xFFFFFF))))[2:] +\
                    str(hex(int(255 * FLIGHTPATH_PERCENT_OPAQUE/100)))[2:]
            # A convaluted way of starting at 2 and reserving 5 id numbers per style
            id_base = (flight_num + 2) * 5 - 2
            elem_doc.append(self.create_style_elem(
                color, color, id_base-2, id_base-1, id_base
            ))
            elem_doc.append(self.create_flight_plot(
                id_base-4, flight_num+1, id_base-2, id_base-3, flightcoords[flight_num]
            ))

        kml_tree.write(outfile_name)
        print(f"Done writing {outfile_name}")
