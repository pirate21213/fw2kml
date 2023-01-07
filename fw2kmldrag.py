import sys, logging, csv, operator, datetime, time
from pathlib import Path

# Global variables
totalflights = 1    # Number of detected flights, used for color coordination (currently uses time gaps)
badtimedata = False

try:
    droppedFile = Path(sys.argv[1])
    #droppedFile = 'TestCases/timejitter.csv'
    print(droppedFile)

    # load csv into memory (top row becomes fields)
    rows = []
    fields = []
    with open(droppedFile, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        fields = next(csvreader)
        for row in csvreader:
            rows.append(row)

    # Figure out which field is alt, lon, and lat
    latindex = fields.index("LAT")
    lonindex = fields.index("LON")
    altindex = fields.index("ALT")
    try:
        # Attempt to find UNIXTIME, first format given to me does not include this field.
        unixtimeindex = fields.index("UNIXTIME")
        rows = sorted(rows, key=operator.itemgetter(unixtimeindex))
    except ValueError:
        print("No unixtime field found, Looking for 'TIME'")
        try:
            timeindex = fields.index("TIME")
            dateindex = fields.index("DATE")

            # Convert DATE and TIME into UNIXTIME (will reuse the TIME field temporarily)
            for row in rows:
                dt = "{}_{}".format(row[dateindex], row[timeindex]) # Concat date and time into a usable string
                row[timeindex] = time.mktime(datetime.datetime.strptime(dt, "%Y-%m-%d_%H:%M:%S.%f").timetuple())  # convert time field into unixtime   Example: 2022-11-05_10:43:00.789 to UNIXTIME
                # print("DATE+TIME: {} to UNIX: {}".format(dt, row[timeindex]))
            unixtimeindex = fields.index("TIME")
            rows = sorted(rows, key=operator.itemgetter(unixtimeindex))
        except ValueError:
            print("Could not find TIME or DATE, will not sort for time jitter or split flights.")
            badtimedata = True

    # ------------------- rows after this point should be sorted by UNIXTIME ----------------------

    # Create output .kml in same directory is input .csv
    outfile_name = str(droppedFile).replace('.csv', '_fw2kml.kml')
    # Create list of coordinates that pass error check
    coords = []
    flightcoords = []
    lasttimeUNIX = rows[1][unixtimeindex]   # instantiate lasttimeUNIX to first timestamp
    for row in rows:
        if float(row[5]) <= 0:
            print("Bad data, skipping", row[5])
        else:
            if badtimedata or float(row[unixtimeindex])-float(lasttimeUNIX) < 60:  # If 1 minute goes by, consider it a new flight - If theres badtimedata, just let it dump everything into one coordstring
                coords.append("{},{},{}".format(row[lonindex], row[latindex], (int(row[altindex]) * 0.3048)))
            else:
                print("New flight detected")
                totalflights += 1
                coordstring = ' '.join(coords)
                flightcoords.append(coordstring)
                coords = []
        lasttimeUNIX = row[unixtimeindex]

    # Convert coordinate list into coordinate string with ' ' as delimiter
    coordstring = ' '.join(coords)
    flightcoords.append(coordstring)

    print(flightcoords)
    # Open output file and write kml header data and format coordinate string into <coordinates></coordinates>
    f = open(outfile_name, "w")
    # KML header
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">\n\t<Document id="1">')
    # Line Styles
    f.write('\n\t\t<Style id="4">\n\t\t\t<LineStyle id="7">\n\t\t\t\t<color>641400F0</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t</LineStyle>\n\t\t\t<PolyStyle id="10">\n\t\t\t\t<color>641400F0</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t\t<fill>1</fill>\n\t\t\t\t<outline>1</outline>\n\t\t\t</PolyStyle>\n\t\t</Style>')
    f.write('\n\t\t<Style id="5">\n\t\t\t<LineStyle id="8">\n\t\t\t\t<color>6414B40A</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t</LineStyle>\n\t\t\t<PolyStyle id="11">\n\t\t\t\t<color>6414B40A</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t\t<fill>1</fill>\n\t\t\t\t<outline>1</outline>\n\t\t\t</PolyStyle>\n\t\t</Style>')
    f.write('\n\t\t<Style id="6">\n\t\t\t<LineStyle id="9">\n\t\t\t\t<color>64F01414</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t</LineStyle>\n\t\t\t<PolyStyle id="12">\n\t\t\t\t<color>64F01414</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t\t<fill>1</fill>\n\t\t\t\t<outline>1</outline>\n\t\t\t</PolyStyle>\n\t\t</Style>')

    # Coordinates of flights
    for i in range(0, totalflights):
        f.write('\n\t\t<open>1</open>\n\t\t<Placemark id="{}">\n\t\t\t<name>fw2kml - Flight {}</name>\n\t\t\t<styleUrl>#{}</styleUrl>\n\t\t\t<LineString id="{}">\n\t\t\t\t<extrude>1</extrude>\n\t\t\t\t<altitudeMode>absolute</altitudeMode>\n\t\t\t\t<coordinates>{}</coordinates>\n\t\t\t</LineString>\n\t\t</Placemark>'.format(
            40+i, i+1, (3+i) % 3 + 4, 60+i, flightcoords[i]))  # Placemark ID, flight ID, Style URL, LineString ID, Coordstring

    # KML footer
    f.write('\n\t</Document>\n</kml>')



except IndexError:
    print("No file dropped.")

'''
except Exception as Argument:
    f = open("Error.txt", 'a')
    f.write("File: {}".format(str(Argument)))
    f.close()
    print("ERROR: " + str(Argument))

'''