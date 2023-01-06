from distutils.core import setup
import py2exe, sys, os

# console = ['fw2kmldrag.py']
sys.argv.append('py2exe')

setup(
    options={'py2exe': {'bundle_files': 1}},
    windows=[
        {
            'script': "fw2kmldrag.py",
            "icon_resources": [(1, "icon.ico")]
        }
    ],
    zipfile=None,
)
