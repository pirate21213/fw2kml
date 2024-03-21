#!/opt/homebrew/bin/python3

"""
GUI for Arpak @TheRocketryForum's Featherweight to KML Converter

Author: Kayla Tokash (Aeva)
Date:   March 21st, 2024

Changelog
---------

 - March 21st, 2024: Initial GUI work
"""


from PyQt5 import QtCore,QtGui
import PyQt5.QtWidgets as qtw
import fw2kmllib

WINDOW_TITLE = "fw2kml utility"
PERMITTED_FILE_EXTS = ["csv"]

class DragAndDropGui(qtw.QMainWindow):
    tool = None

    def __init__(self):
        super().__init__();
        self.tool = fw2kmllib.fw2kml()
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(0,0,300,300)
        self.setAcceptDrops(True)

        self.layout = qtw.QVBoxLayout()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            ext = url.path().split(".")[-1]
            if ext in PERMITTED_FILE_EXTS:
                self.tool.convertFile(url.toLocalFile())
            else:
                print(f"Error: Invalid file extension \"{ext}\" dropped on conversion tool. Skipping {url}.")
                print(f"Allowed EXTS: {PERMITTED_FILE_EXTS}")

if __name__ == "__main__":
    app = qtw.QApplication([])
    gui = DragAndDropGui()
    gui.show()
    app.exec()
