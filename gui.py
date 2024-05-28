"""
GUI for Arpak @TheRocketryForum's Featherweight to KML Converter

Author(s): Aeva (Kayla Tokash)

Changelog
---------

 - March 21st, 2024: Initial GUI work

"""

from os import path
from PyQt5 import QtGui #,QtCore
import PyQt5.QtWidgets as qtw
import fw2kmllib

WINDOW_TITLE = "fw2kml utility"
PERMITTED_FILE_EXTS = ["csv"]
ICON_PATH = path.dirname(path.realpath(__file__)) + path.sep + 'fancyicon.png'
WINDOW_HEIGHT_WIDTH = (300, 300)

class DragAndDropGui(qtw.QMainWindow):
    """
    DragAndDrogGui Class for PyQT5 GUI
    """

    tool = None

    def __init__(self):
        super().__init__()

        # Create fw2kml tool from library
        self.tool = fw2kmllib.fw2kml()

        # Create GUI with PyQT5
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(0,0,*WINDOW_HEIGHT_WIDTH)
        self.setAcceptDrops(True)

        logo_icon = QtGui.QPixmap(ICON_PATH)
        self.label_logo = qtw.QLabel(self)
        self.label_logo.setAcceptDrops(True)
        self.label_logo.setPixmap(logo_icon.scaled(*WINDOW_HEIGHT_WIDTH))
        self.label_logo.resize(*WINDOW_HEIGHT_WIDTH)

    # Override "dragEnterEvent" handler
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    # Override "dropEvent" handler
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            ext = url.path().split(".")[-1]
            if ext in PERMITTED_FILE_EXTS:
                self.tool.convert_file(url.toLocalFile())
            else:
                print(f"Error: Invalid file extension \"{ext}\" " +\
                        f"dropped on conversion tool. Skipping {url}.")
                print(f"Allowed EXTS: {PERMITTED_FILE_EXTS}")

# Allow application from script or import
if __name__ == "__main__":
    app = qtw.QApplication([])
    gui = DragAndDropGui()
    gui.show()
    app.setWindowIcon(QtGui.QIcon(ICON_PATH))
    app.exec()
