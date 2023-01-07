import sys, logging, csv, operator
from pathlib import Path
try:
    droppedFile = Path(sys.argv[1])
    #droppedFile = 'TestCases/timejitter.csv'
    print(droppedFile)
    '''
    f = open(droppedFile, 'r')
    data = f.readlines()[19:]
    f.close()
    print(data[0:10])

    out_data = []
    for d in data:
        split = d.split('\n')[0]
        split = d.split('\t')[0:2]
        out_data.append(split)
    print(out_data[:10])
'''
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
        unixtimeindex = fields.index("UNIXTIME")
        rows = sorted(rows, key=operator.itemgetter(unixtimeindex))
    except ValueError:
        print("No unixtime field found, will not sort for time jitter.")

    outfile_name = str(droppedFile).replace('.csv', '_fw2kml.kml')
    coords = []
    for row in rows:
        if int(row[5]) <= 0:
            print("Bad data, skipping", row[5])
        else:
            coords.append("{},{},{}".format(row[lonindex], row[latindex], (int(row[altindex]) * 0.3048)))

    coordstring = ' '.join(coords)

    f = open(outfile_name, "w")
    f.write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">\n\t<Document id="1">\n\t\t<Style id="4">\n\t\t\t<LineStyle id="5">\n\t\t\t\t<color>641400F0</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t</LineStyle>\n\t\t\t<PolyStyle id="6">\n\t\t\t\t<color>641400F0</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t\t<fill>1</fill>\n\t\t\t\t<outline>1</outline>\n\t\t\t</PolyStyle>\n\t\t</Style>\n\t\t<open>1</open>\n\t\t<Placemark id="3">\n\t\t\t<name>fw2kml</name>\n\t\t\t<styleUrl>#4</styleUrl>\n\t\t\t<LineString id="2">\n\t\t\t\t<extrude>1</extrude>\n\t\t\t\t<altitudeMode>absolute</altitudeMode>\n\t\t\t\t<coordinates>{}</coordinates>\n\t\t\t</LineString>\n\t\t</Placemark>\n\t</Document>\n</kml>'.format(
            coordstring))



except IndexError:
    print("No file dropped.")
    #droppedFile = '20220329_POC1_DualCeramic_Ti100-10.6-Fan_CW-PowerData.csv'
    #output = open("formatted_{}".format(droppedFile), "a")
    #output.close()

except Exception as Argument:
    f = open("Error.txt", 'a')
    f.write("File: {}".format(str(Argument)))
    f.close()

