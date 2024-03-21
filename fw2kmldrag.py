import fw2kmllib
from sys import argv

if len(argv) > 1:
    tool = fw2kmllib.fw2kml()
    for file_path in argv[1:]:
        tool.convertFile(file_path)
