"""
Run this file or the following code to show this example.

import studiolibrary
from studiolibraryexamples import example1
reload(example1)
example1.main()
"""
import os

import studiolibrary
import studiolibraryitems

# studioqt supports both pyside (Qt4) and pyside2 (Qt5)
import studioqt
from studioqt import QtGui
from studioqt import QtCore
from studioqt import QtWidgets


# At the moment all paths need to have forward slashes
dirname = os.path.dirname(__file__).replace("\\", "/")


class MayaFileItem(studiolibrary.LibraryItem):

    """An item to display jpg/png in the Studio Library."""

    def load(self):
        """ Trigged when the user double clicks or clicks the load button."""
        print "Loaded", self.path()

    def doubleClicked(self):
        """Overriding this method to load any data on double click."""
        self.load()

    def thumbnailPath(self):
        """
        Return the thumbnail path to be displayed for the item.

        :rtype: str
        """
        name = self.name()

        path = self.dirname() + "/.mayaSwatches/" + name + ".swatch"

        if not os.path.isfile(path):
            path = self.dirname() + "/.mayaSwatches/" + name + ".preview"

        if not os.path.isfile(path):
            path = studiolibraryitems.resource().get("icons", "maFileIcon.png")

        return path

    def imageSequencePath(self):
        """
        Return the image sequence location for playing the animation preview.

        :rtype: str
        """
        name = self.name()
        return self.dirname() + "/.mayaSwatches/" + name

    def previewWidget(self, libraryWidget):
        """
        Return the widget to be shown when the user clicks on the item.

        :type libraryWidget: studiolibrary.LibraryWidget
        :rtype: CreateWidget
        """
        return ImagePreviewWidget(self)


class ImagePreviewWidget(QtWidgets.QWidget):

    """The widget to be shown when the user clicks on an image item."""

    def __init__(self, item, *args):
        """
        :type item: ImageItem
        :type args: list
        """
        QtWidgets.QWidget.__init__(self, *args)

        self._item = item
        self._pixmap = QtGui.QPixmap(item.thumbnailPath())

        self._image = QtWidgets.QLabel(self)
        self._image.setAlignment(QtCore.Qt.AlignHCenter)

        self._loadButton = QtWidgets.QPushButton("Load")
        self._loadButton.setFixedHeight(40)
        self._loadButton.clicked.connect(self.load)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._image)
        layout.addStretch(1)
        layout.addWidget(self._loadButton)

        self.setLayout(layout)

    def load(self):
        """Triggered when the user clicks the load button."""
        self._item.load()

    def resizeEvent(self, event):
        """
        Overriding to adjust the image size when the widget changes size.

        :type event: QtCore.QSizeEvent
        """
        width = self.width() / 1.2
        transformMode = QtCore.Qt.SmoothTransformation
        pixmap = self._pixmap.scaledToWidth(width, transformMode)
        self._image.setPixmap(pixmap)


studiolibrary.register(MayaFileItem, ".ma", isDir=False)
studiolibrary.register(MayaFileItem, ".mb", isDir=False)


def main():
    """The main entry point for this example."""
    with studioqt.app():
        studiolibrary.main(name="Example", path=dirname + "/")


if __name__ == "__main__":
    main()