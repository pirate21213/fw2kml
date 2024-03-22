from distutils.core import setup
import py2exe
import sys
import os
import zipfile

"""
NOTE: I have no idea how py2exe works, so I'm winging it. I /think/ that
the contents of the zip file are what is added to the bundle. I think this
will create two binaries: one for the drag and drop, and one for the gui.
It's untested...
"""

# Precompile
ZIP_FILE_PATH="./.packaged_files.zip"
ZIP_CONTENTS=["fw2kmllib.py", "fancyicon.png"]

# Clean old archive if it exists
if os.path.isfile(ZIP_FILE_PATH):
    os.remove(ZIP_FILE_PATH)

# Create the zip file with the packages
with zipfile.ZipFile(ZIP_FILE_PATH, mode="w") as archive:
    for file in ZIP_CONTENTS:
        archive.write(file)

# Build Windows Executable
sys.argv.append("py2exe")
setup(
    options={"py2exe": {"bundle_files": 1}},
    windows=[
        {
            "dest_base": "fw2kwl_dragNdrop",
            "script": "fw2kmldrag.py",
            "icon_resources": [(1, "icon.ico")]
        },
        {
            "dest_base": "fw2kwl_gui",
            "script": "gui.py",
            "icon_resources": [(1, "icon.ico")],
        }
    ],
    zipfile=ZIP_FILE_PATH,
)
