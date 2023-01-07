import sys, logging, csv, operator
from pathlib import Path

# Change "inputData" to the file location of the data you'd like to process
inputData = 'TestCases/timejitter.csv'

try:
    print(inputData)

    # load csv into memory (top row becomes fields)
    rows = []
    fields = []
    with open(inputData, 'r') as csvfile:
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
        print("No unixtime field found, will not sort for time jitter.")

    # Create output .kml in same directory is input .csv
    outfile_name = str(inputData).replace('.csv', '_fw2kml.kml')

    # Create list of coordinates that pass error check
    coords = []
    for row in rows:
        if int(row[5]) <= 0:
            print("Bad data, skipping", row[5])
        else:
            coords.append("{},{},{}".format(row[lonindex], row[latindex], (int(row[altindex]) * 0.3048)))

    # Convert coordinate list into coordinate string with ' ' as delimiter
    coordstring = ' '.join(coords)

    # Open output file and write kml header data and format coordinate string into <coordinates></coordinates>
    f = open(outfile_name, "w")
    f.write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">\n\t<Document id="1">\n\t\t<Style id="4">\n\t\t\t<LineStyle id="5">\n\t\t\t\t<color>641400F0</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t</LineStyle>\n\t\t\t<PolyStyle id="6">\n\t\t\t\t<color>641400F0</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t\t<fill>1</fill>\n\t\t\t\t<outline>1</outline>\n\t\t\t</PolyStyle>\n\t\t</Style>\n\t\t<open>1</open>\n\t\t<Placemark id="3">\n\t\t\t<name>fw2kml</name>\n\t\t\t<styleUrl>#4</styleUrl>\n\t\t\t<LineString id="2">\n\t\t\t\t<extrude>1</extrude>\n\t\t\t\t<altitudeMode>absolute</altitudeMode>\n\t\t\t\t<coordinates>{}</coordinates>\n\t\t\t</LineString>\n\t\t</Placemark>\n\t</Document>\n</kml>'.format(
            coordstring))



except IndexError:
    print("No file dropped.")

except Exception as Argument:
    f = open("Error.txt", 'a')
    f.write("File: {}".format(str(Argument)))
    f.close()

