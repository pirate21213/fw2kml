#!/opt/homebrew/bin/python3

from PyQt5 import QtCore,QtGui
import PyQt5.QtWidgets as qtw
import fw2kmllib

WINDOW_TITLE = "fw2kml utility"

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
            self.tool.convertFile(url.toLocalFile())



if __name__ == "__main__":
    app = qtw.QApplication([])
    gui = DragAndDropGui()
    gui.show()
    app.exec()
