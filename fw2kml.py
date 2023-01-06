import csv

# csv file name
filename = "input.csv"
rows = []

with open(filename, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)
    for row in csvreader:
        rows.append(row)

coords = []
for row in rows:
    if int(row[5]) <= 0:
        print("Bad data, skipping", row[5])
    else:
        coords.append("{},{},{}".format(row[4], row[3], (int(row[5])*0.3048)))

coordstring = ' '.join(coords)

f = open("fw2kml.kml", "w")
f.write('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">\n\t<Document id="1">\n\t\t<Style id="4">\n\t\t\t<LineStyle id="5">\n\t\t\t\t<color>641400F0</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t</LineStyle>\n\t\t\t<PolyStyle id="6">\n\t\t\t\t<color>641400F0</color>\n\t\t\t\t<colorMode>normal</colorMode>\n\t\t\t\t<fill>1</fill>\n\t\t\t\t<outline>1</outline>\n\t\t\t</PolyStyle>\n\t\t</Style>\n\t\t<open>1</open>\n\t\t<Placemark id="3">\n\t\t\t<name>fw2kml</name>\n\t\t\t<styleUrl>#4</styleUrl>\n\t\t\t<LineString id="2">\n\t\t\t\t<extrude>1</extrude>\n\t\t\t\t<altitudeMode>absolute</altitudeMode>\n\t\t\t\t<coordinates>{}</coordinates>\n\t\t\t</LineString>\n\t\t</Placemark>\n\t</Document>\n</kml>'.format(coordstring))

