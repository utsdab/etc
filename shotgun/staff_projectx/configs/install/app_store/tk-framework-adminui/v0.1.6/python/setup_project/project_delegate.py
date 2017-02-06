# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk

from tank.platform.qt import QtGui
from tank.platform.qt import QtCore

from . import project_model

views = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")


class ProjectWidget(QtGui.QFrame):
    """ Simple widget that shows a project's thumbnail and name. """
    MARGIN = 5
    ICON_SIZE = QtCore.QSize(32, 32)

    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent)

        # initialize the UI
        # simple frame with a thumbnail and a label
        self.setObjectName("frame")
        self.setFrameStyle(self.NoFrame)
        self.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)

        self.label = QtGui.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        self.label.setWordWrap(True)

        self.thumbnail = QtGui.QLabel(self)
        self.thumbnail.setScaledContents(True)

        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.thumbnail)
        self.layout.addWidget(self.label)
        self.layout.setStretchFactor(self.label, 1)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.layout)
        self.setVisible(False)
        self.set_selected(False)

    def set_thumbnail(self, pixmap):
        scaled = pixmap.scaled(self.ICON_SIZE, QtCore.Qt.KeepAspectRatio)
        self.thumbnail.setPixmap(scaled)

    def set_text(self, label):
        metrics = QtGui.QFontMetrics(self.label.font())
        elided = metrics.elidedText(label, QtCore.Qt.ElideMiddle, self.label.width())
        self.label.setText(elided)
        self.setToolTip(label)

    def set_selected(self, selected):
        """ Update the styling to reflect if the widget is selected or not """
        if selected:
            p = QtGui.QPalette()
            highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)

            transp_highlight_str = "rgba(%s, %s, %s, 25%%)" % \
                (highlight_col.red(), highlight_col.green(), highlight_col.blue())
            highlight_str = "rgb(%s, %s, %s)" % \
                (highlight_col.red(), highlight_col.green(), highlight_col.blue())

            # make a border around the cell
            self.setStyleSheet(
                """#frame {
                    border-width: 2px;
                    border-color: %s;
                    border-style: solid;
                    background-color: %s;
                   }
                """ % (highlight_str, transp_highlight_str))
        else:
            self.setStyleSheet(
                """#frame {
                      border-width: 2px;
                      border-color: transparent;
                      border-style: solid;
                }""")


class ProjectDelegate(views.EditSelectedWidgetDelegate):
    """ Wrapper around the ProjectWidget for delegate use """
    def __init__(self, view):
        views.EditSelectedWidgetDelegate.__init__(self, view)

    def _create_widget(self, parent):
        return ProjectWidget(parent)

    def _on_before_paint(self, widget, model_index, style_options):
        if (style_options.state & QtGui.QStyle.State_Selected):
            widget.set_selected(True)
        else:
            widget.set_selected(False)

        icon = model_index.data(QtCore.Qt.DecorationRole)
        if icon is not None:
            thumb = icon.pixmap(30)
            widget.set_thumbnail(thumb)
        widget.set_text(model_index.data(project_model.ProjectModel.DISPLAY_NAME_ROLE))

    def _on_before_selection(self, widget, model_index, style_options):
        self._on_before_paint(widget, model_index, style_options)

    def sizeHint(self, style_options, model_index):
        return QtCore.QSize(175, 2*ProjectWidget.MARGIN + ProjectWidget.ICON_SIZE.height())
