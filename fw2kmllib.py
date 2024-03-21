"""
Library for Arpak @TheRocketryForum's Featherweight to KML Converter

Author(s): Arpak, Aeva

Changelog
---------

 - March 21st, 2024: Updated Arpak's code for use with a gui

"""

import sys, logging, csv, operator, datetime, time
from pathlib import Path
from os import path

class fw2kml():
    """
    fw2kml util class
    """
    def __init__(self):
        pass
        #tbh, we can probably make this class a function "convertFile" instead

    def convertFile(self, droppedFile):
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
            print("Necessary fields for latitude, longitude, and altitude are missing. Cannot process file.")
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
                dt = "{}_{}".format(row[dateindex], row[timeindex]) # Concat date and time into a usable string
                row[timeindex] = time.mktime(datetime.datetime.strptime(dt, "%Y-%m-%d_%H:%M:%S.%f").timetuple())  # convert time field into unixtime   Example: 2022-11-05_10:43:00.789 to UNIXTIME
                # print("DATE+TIME: {} to UNIX: {}".format(dt, row[timeindex]))
            unixtimeindex = fields.index("TIME")
            rows = sorted(rows, key=operator.itemgetter(unixtimeindex))
        else:
            print("Could not find TIME or DATE, will not sort for time jitter or split flights.")
            badtimedata = True

        # ------------------- rows after this point should be sorted by UNIXTIME ----------------------

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
        with open(outfile_name, "w") as outfile:
            # Open output file and write kml header data and format coordinate
            # string into <coordinates></coordinates>

            # KML header
            outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">\n\t<Document id="1">')

            # Line Styles
            outfile.write('\n\t\t<Style id="4">\n\t\t\t<LineStyle id="7">\n\t\t\t\t<color>641400F0</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t</LineStyle>\n\t\t\t<PolyStyle id="10">\n\t\t\t\t<color>641400F0</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t\t<fill>1</fill>\n\t\t\t\t<outline>1</outline>\n\t\t\t</PolyStyle>\n\t\t</Style>')
            outfile.write('\n\t\t<Style id="5">\n\t\t\t<LineStyle id="8">\n\t\t\t\t<color>6414B40A</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t</LineStyle>\n\t\t\t<PolyStyle id="11">\n\t\t\t\t<color>6414B40A</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t\t<fill>1</fill>\n\t\t\t\t<outline>1</outline>\n\t\t\t</PolyStyle>\n\t\t</Style>')
            outfile.write('\n\t\t<Style id="6">\n\t\t\t<LineStyle id="9">\n\t\t\t\t<color>64F01414</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t</LineStyle>\n\t\t\t<PolyStyle id="12">\n\t\t\t\t<color>64F01414</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t\t<fill>1</fill>\n\t\t\t\t<outline>1</outline>\n\t\t\t</PolyStyle>\n\t\t</Style>')

            # Coordinates of flights
            for i in range(0, totalflights):
                outfile.write('\n\t\t<open>1</open>\n\t\t<Placemark id="{}">\n\t\t\t<name>fw2kml - Flight {}</name>\n\t\t\t<styleUrl>#{}</styleUrl>\n\t\t\t<LineString id="{}">\n\t\t\t\t<extrude>1</extrude>\n\t\t\t\t<altitudeMode>absolute</altitudeMode>\n\t\t\t\t<coordinates>{}</coordinates>\n\t\t\t</LineString>\n\t\t</Placemark>'.format(
                    40+i, i+1, (3+i) % 3 + 4, 60+i, flightcoords[i]))  # Placemark ID, flight ID, Style URL, LineString ID, Coordstring

            # KML footer
            outfile.write('\n\t</Document>\n</kml>')

        print("Done")
