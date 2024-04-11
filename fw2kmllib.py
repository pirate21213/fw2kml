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

# Constant Configs

# How visible the flight path
FLIGHTPATH_PERCENT_OPAQUE = 75

# Just a name for the pins for common use
PIN_STYLE_NAME="PUSH_PIN"

# Used for event pins
TRIGGER_VSPEED_LAUNCH_FPS=2

# Decent speed recovery detection, if acceleration is greater than
# this number it resets the detection until it falls below that number
# In theory, there should be zero acceleration when a chute reaches
# terminal velocity, and when the rocket has landed
TRIGGER_ACCEL_VERT_RECOVERY_FPS=10
# To detect if the rocket is falling
TRIGGER_VSPEED_RECOVERY_FPS=-1

# Number of rows to check before adding a recovery deployment
# Prevents false positives
RD_CHECK_ROWS = 5


feet_to_meters = lambda feet_str: float(feet_str) * 0.3048

class fw2kml():
    """
    fw2kml util class
    """

    def __init__(self):
        pass

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
        coorlist = SubElement(elem_lenstr, "coordinates")
        coorlist.text = coordinates
        return elem_mark

    @staticmethod
    def create_pin(event_id, name, coordinates, pin_style=PIN_STYLE_NAME):
        elem_mark = Element("Placemark", attrib={"id":f"{event_id}"})
        elem_name = SubElement(elem_mark, "name")
        elem_name.text = name
        elem_style = SubElement(elem_mark, "styleUrl")
        elem_style.text = f"#{pin_style}"
        elem_point = SubElement(elem_mark, "Point")
        altmode = SubElement(elem_point, "altitudeMode")
        altmode.text = "absolute"
        elem_coor = SubElement(elem_point, "coordinates")
        elem_coor.text = " ".join(coordinates)
        return elem_mark

    @staticmethod
    def generate_pin_style(style_name=PIN_STYLE_NAME, icon_href= \
            "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png"):
        elem_style = Element("Style", attrib={"id":f"{style_name}"})
        elem_icostyle = SubElement(elem_style, "IconStyle", attrib={"id":f"ICON_{style_name}"})
        elem_icon = SubElement(elem_icostyle, "Icon")
        elem_href = SubElement(elem_icon, "href")
        elem_href.text = icon_href
        elem_scale = SubElement(elem_icon, "scale")
        elem_scale.text = "1.0"

        return elem_style

    @staticmethod
    def process_coordinates(data_rows, column_indicies, export_from_ifip, badtimedata):
        coords = []
        flightcoords = []
        max_altitude = []
        launch_site = []
        recovery_site = []
        launch_time = []
        recovery_deployments = [[]]
        vert_speed = [[]]
        decent_speed_changed = False
        last_recovery_detected = None

        for i, row in enumerate(data_rows):
            # unclear what it's skipping for
            if export_from_ifip and float(row[5]) <= 0:
                print("Bad data, skipping", row[5])
            elif row[column_indicies["unixtime"]] == data_rows[i-1][column_indicies["unixtime"]]:
                # Skip duplicates; I've notice these cause problems with post processing, and 
                # add more data needlessly to the file
                continue
            else:
                # If 1 minute goes by, consider it a new flight - If theres badtimedata, just
                # let it dump everything into one coordstring
                if badtimedata or i == 0 or\
                    float(row[column_indicies["unixtime"]])-float(last_time_unix) < 60:
                    if len(coords) > 0:
                        vert_speed[-1].append(float(row[column_indicies["alt"]]) -
                            float(data_rows[i-1][column_indicies["alt"]]))
                        if vert_speed[-1][-1] > TRIGGER_VSPEED_LAUNCH_FPS and \
                            len(launch_time) < len(vert_speed):
                            launch_time.append(
                                {"unixtime":data_rows[i-1][column_indicies["unixtime"]],
                                "coord":(data_rows[i-1][column_indicies["lon"]],
                                        data_rows[i-1][column_indicies["lat"]],
                                        data_rows[i-1][column_indicies["alt"]])})

                        # When the acceleration jumps, and the rocket has launched,
                        # guess we had recovery deployment
                        if len(coords) > 1 and len(launch_time) == len(vert_speed) \
                            and decent_speed_changed and vert_speed[-1][-1] <\
                            TRIGGER_VSPEED_RECOVERY_FPS:
                            last_recovery_detected = (i,
                                {"unixtime":row[column_indicies["unixtime"]],
                                 "coord":(row[column_indicies["lon"]],
                                          row[column_indicies["lat"]],
                                          row[column_indicies["alt"]])})
                            decent_speed_changed = False
                        elif len(launch_time) == len(vert_speed) and abs(vert_speed[-1][-2] -\
                                vert_speed[-1][-1]) > TRIGGER_ACCEL_VERT_RECOVERY_FPS:
                            decent_speed_changed = True
                        elif last_recovery_detected is not None and\
                            (i - last_recovery_detected[0] > RD_CHECK_ROWS or\
                            i == len(data_rows) - 1):
                            # Parachutes are finicky (sp?) so it's best to check a few rows first
                            recovery_deployments[-1].append(last_recovery_detected[1])
                            last_recovery_detected = None

                    altitude_meters = str(feet_to_meters(row[column_indicies["alt"]]))
                    coords.append("{},{},{}".format(
                        row[column_indicies["lon"]], row[column_indicies["lat"]], altitude_meters))

                    # Using first data point as launch site location for first flight
                    if i == 0:
                        launch_site.append((row[column_indicies["lon"]],
                            row[column_indicies["lat"]], row[column_indicies["alt"]]))

                    # Checking for apogee
                    if len(max_altitude) < len(flightcoords) + 1:
                        max_altitude.append({"unixtime":row[column_indicies["unixtime"]],
                            "coord":(row[column_indicies["lon"]],
                            row[column_indicies["lat"]], row[column_indicies["alt"]])})
                    elif float(max_altitude[len(flightcoords)]["coord"][2]) <\
                            float(row[column_indicies["alt"]]):
                        max_altitude[len(flightcoords)] = {"unixtime":
                            row[column_indicies["unixtime"]], "coord":(row[column_indicies["lon"]],
                            row[column_indicies["lat"]], row[column_indicies["alt"]])}
                else:
                    # Use last data point as recovery site location
                    recovery_site.append((data_rows[i-1][column_indicies["lon"]],
                        data_rows[i-1][column_indicies["lat"]],
                        data_rows[i-1][column_indicies["alt"]]))

                    # Iterate flight data
                    flightcoords.append(' '.join(coords))
                    vert_speed.append([])
                    recovery_deployments.append([])
                    coords = []

                    # Add new launch site
                    launch_site.append((row[column_indicies["lon"]], row[column_indicies["lat"]],
                        row[column_indicies["alt"]]))

            last_time_unix = row[column_indicies["unixtime"]]

        # Once we leave the loop block we have to do this too for the last flight in file
        recovery_site.append((data_rows[-1][column_indicies["lon"]],
            data_rows[-1][column_indicies["lat"]], data_rows[-1][column_indicies["alt"]]))

        # Convert coordinate list into coordinate string with ' ' as delimiter
        coordstring = ' '.join(coords)
        flightcoords.append(coordstring)

        events = {"launch_site":launch_site,"apogee":max_altitude,"recovery_site":recovery_site,
                  "launch_time":launch_time,"recovery_deployments":recovery_deployments}

        return (len(flightcoords), flightcoords, events)

    @staticmethod
    def get_unused_filename(dropped_file):
        # Determine the outputed file's name
        file_basename = ".".join(str(dropped_file).split(".")[:-1])
        new_ext = "_fw2kml.kml"
        num_converted = 0
        outfile_name = None
        while True:
            outfile_name = f"{file_basename}_{num_converted}{new_ext}"
            if not path.isfile(Path(outfile_name)):
                break
            num_converted += 1
        return outfile_name

    @staticmethod
    def get_random_rgba_color(percent_opaque=FLIGHTPATH_PERCENT_OPAQUE):
        # FIXME For some reason this generates a transparent color occassionally
        # Super lazy way to generate random colors
        # basically doing randhex(0x0, 0xFFFFFF) but in decimal
        color = str(hex(randint(0,int(0xFFFFFF))))[2:].rjust(6, '0') +\
                str(hex(int(255 * percent_opaque/100)))[2:].rjust(2, '0')
        return color

    def create_kml_elementtree(self, totalflights, flightcoords, events):
        kml_tree = ElementTree()
        elem_kml = Element("kml", attrib={
                "xmlns":"http://www.opengis.net/kml/2.2",
                "xmlns:gx":"http://www.google.com/kml/ext/2.2"
            }
        )
        # pylint doesn't like this, and it seems to be unrecommended to do this
        kml_tree._setroot(elem_kml)

        elem_doc = SubElement(elem_kml, "Document", attrib={"id":"1"})

        elem_name = SubElement(elem_doc, "Name")
        elem_name.text = "fw2kml FeatherWeight KML"

        # generate pin style
        elem_doc.append(self.generate_pin_style())

        for flight_num in range(totalflights):
            flight_id = flight_num+1

            # Generate flight plot
            # A convaluted way of starting at 2 and reserving 5 id numbers per style
            id_base = (flight_num + 2) * 5 - 2
            color = self.get_random_rgba_color()
            elem_doc.append(self.create_style_elem(
                color, color, id_base-2, id_base-1, id_base
            ))
            elem_doc.append(self.create_flight_plot(
                id_base-4, flight_id, id_base-2, id_base-3, flightcoords[flight_num]
            ))

            # Generate launchsite pin
            launch_site = events["launch_site"][flight_num]
            elem_doc.append(self.create_pin(f"launchsite_{flight_id}",
                f"Flight #{flight_id} Launch Site",
                (str(launch_site[0]), str(launch_site[1]), str(feet_to_meters(launch_site[2])))))

            # Generate launch pin
            launch_time = events["launch_time"][flight_num]
            elem_doc.append(self.create_pin(f"launchpin_{flight_id}",
                f"Flight #{flight_id} Launch Time T+0",
                (str(launch_time["coord"][0]), str(launch_time["coord"][1]),
                 str(feet_to_meters(launch_time["coord"][2])))))

            # Generate apogee pin
            apogee = events["apogee"][flight_num]
            apogee_alt_feet = float(apogee["coord"][2]) - float(launch_site[2])
            time_past_launch = float(apogee["unixtime"]) -\
                    float(events["launch_time"][flight_num]["unixtime"])
            elem_doc.append(self.create_pin(f"apogee_{flight_id}",
                f"Flight #{flight_id} Apogee {apogee_alt_feet:.2f}ft, T+{time_past_launch:.2f}s",
                (str(apogee["coord"][0]), str(apogee["coord"][1]),
                 str(feet_to_meters(apogee["coord"][2])))))

            # Generate recovery device pins
            recovery_deployments = events["recovery_deployments"][flight_num]
            for num, deployment in enumerate(recovery_deployments):
                time_past_launch = float(deployment["unixtime"]) -\
                        float(events["launch_time"][flight_num]["unixtime"])
                if num == len(recovery_deployments) - 1:
                    # Assume we've landed
                    elem_doc.append(self.create_pin(f"landing_{flight_id}",
                        f"Flight #{flight_id} Landing T+{time_past_launch:.2f}s",
                        (str(deployment["coord"][0]), str(deployment["coord"][1]),
                         str(feet_to_meters(deployment["coord"][2])))))
                else:
                    recovery_alt_feet = float(deployment["coord"][2]) - float(launch_site[2])
                    # Presume we had recovery deployment
                    elem_doc.append(self.create_pin(f"recovery_{num}_{flight_id}",
                        f"Flight #{flight_id} Deployment #{num+1} {recovery_alt_feet:.2f}ft,"+
                        f" T+{time_past_launch:.2f}s",
                        (str(deployment["coord"][0]), str(deployment["coord"][1]),
                         str(feet_to_meters(deployment["coord"][2])))))

            # Generate recovery site pin
            recovery_site = events["recovery_site"][flight_num]
            elem_doc.append(self.create_pin(f"recoverysite_{flight_id}",
                f"Flight #{flight_id} Recovery Site", (str(recovery_site[0]),
                str(recovery_site[1]), str(feet_to_meters(recovery_site[2])))))

        return kml_tree

    @staticmethod
    def load_and_process_csv(filename):
        # load csv into memory (top row becomes fields)
        rows = []
        fields = []
        with open(filename, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            fields = next(csvreader)
            for row in csvreader:
               # Skip rows with column header names
                if "DATE" in row: continue
                rows.append(row)

        return rows, fields

    def convert_file(self, dropped_file):
        """
        convertFile(dropped_file)
        convert the contents of a file from FeatherWeightCSV to Google Maps KML
        dropped_file - (str) path to file to be converted
        """
        # instance variables
        badtimedata = False

        # Load data from FW csv
        rows, fields = self.load_and_process_csv(dropped_file)

        # Figure out which field is alt, lon, and lat
        column_indicies = {
            "lat":None,
            "lon":None,
            "alt":None,
            "unixtime":None,
            "time":None,
            "date":None
        }

        export_from_ifip = True
        for column_name in ["LAT", "LON", "ALT"]:
            if column_name not in fields:
                export_from_ifip = False
                break

        export_blue_raven = not export_from_ifip
        if not export_from_ifip:
            for column_name in ["TRACKER Lat", "TRACKER Lon", "TRACKER Alt asl"]:
                if column_name not in fields:
                    export_blue_raven = False
                    break

        if export_from_ifip:
            column_indicies["lat"] = fields.index("LAT")
            column_indicies["lon"] = fields.index("LON")
            column_indicies["alt"] = fields.index("ALT")
            if "UNIXTIME" in fields:
                column_indicies["unixtime"] = fields.index("UNIXTIME")
            elif "TIME" in fields and "DATE" in fields:
                column_indicies["time"] = fields.index("TIME")
                column_indicies["date"] = fields.index("DATE")
                column_indicies["unixtime"] = fields.index("TIME")
        elif export_blue_raven:
            column_indicies["lat"] = fields.index("TRACKER Lat")
            column_indicies["lon"] = fields.index("TRACKER Lon")
            column_indicies["alt"] = fields.index("TRACKER Alt asl")
            column_indicies["time"] = fields.index("TIME")
            column_indicies["date"] = fields.index("DATE")
            column_indicies["unixtime"] = fields.index("TIME")
        else:
            print("Cannot process file. Necessary columns are missing/not labeled.")
            print("Currently only acccepts csv exports from iFIP and Blue Raven.")
            return

        # TODO move this into a helper function... it depends on "rows" at the moment
        # TODO it seems like time becomes an integer at some point, or the fractions of 
        # a second are lost?
        # which is an instance variable in the convertFile function
        if column_indicies["time"] is not None and column_indicies["date"] is not None:
            # Convert DATE and TIME into UNIXTIME (will reuse the TIME field temporarily)
            for row in rows:
                # Format date and time into a usable string
                formatted_datetime = "{}_{}".format(
                        row[column_indicies["date"]], row[column_indicies["time"]])

                # convert time field into unixtime   Example: 2022-11-05_10:43:00.789 to UNIXTIME
                row[column_indicies["time"]] = time.mktime(datetime.datetime.strptime(
                        formatted_datetime, "%Y-%m-%d_%H:%M:%S.%f").timetuple())

        if column_indicies["unixtime"] is not None:
            rows = sorted(rows, key=operator.itemgetter(column_indicies["unixtime"]))
        else:
            print("Could not find TIME or DATE, will not sort for time jitter or split flights.")
            badtimedata = True

        # Create coordinate list
        totalflights, flightcoords, events = self.process_coordinates(
            rows, column_indicies, export_from_ifip, badtimedata)

        # Get a new filename
        outfile_name = self.get_unused_filename(dropped_file)

        # Create KML file structure in memory
        kml_tree = self.create_kml_elementtree(totalflights, flightcoords, events)

        # Write KML file
        kml_tree.write(outfile_name)
