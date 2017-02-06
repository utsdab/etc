# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys

from sgtk.platform.qt import QtGui

from .base_page import BasePage


class ProjectNamePage(BasePage):
    """ Page to name a project. """
    _HELP_URL = BasePage._HELP_URL + "#Choosing%20a%20project%20folder%20name"

    def __init__(self, parent=None):
        BasePage.__init__(self, parent)
        self.name_valid = False

    def setup_ui(self, page_id):
        BasePage.setup_ui(self, page_id)
        self.wizard().ui.project_name.textChanged.connect(self.on_name_changed)
        self._widget_groups = []

    def initializePage(self):
        wiz = self.wizard()
        name = wiz.core_wizard.get_default_project_disk_name()

        # Reset page state in case back button was used (ie: remove previously created widgets)
        self._storage_path_widgets = {}
        for group in self._widget_groups:
            if wiz.ui.project_contents_layout.indexOf(group) != -1:
                wiz.ui.project_contents_layout.removeWidget(group)
                group.deleteLater()

        self._widget_groups = []

        self.setField("project_name", name)

    def on_name_changed(self, name):
        """ react to the name changing.  Update the paths that will be used. """
        wiz = self.wizard()
        name = self.field("project_name")
        try:
            # Will raise exception if not valid
            wiz.core_wizard.validate_project_disk_name(name)

            # update where the project folders will be for the given name
            project_paths_dict = wiz.core_wizard.preview_project_paths(name)

            # create path widgets if needed
            if not self._storage_path_widgets:
                self._setup_storage_widgets(project_paths_dict)

            # fill out path widgets
            for storage in project_paths_dict:
                for key in ["linux2", "darwin", "win32"]:
                    path = project_paths_dict[storage].get(key)
                    widget = self._storage_path_widgets[storage].get(key)
                    if path and widget:
                        widget.setText(path)
                    elif widget:
                        widget.hide()

            # clear state
            wiz.ui.project_name_errors.setText("")
            self.name_valid = True
        except Exception, e:
            wiz.ui.project_name_errors.setText(str(e))
            self.name_valid = False

        # signal that the next button may have changed state
        self.completeChanged.emit()

    def validatePage(self):
        wiz = self.wizard()
        name = self.field("project_name")
        try:
            wiz.core_wizard.set_project_disk_name(name)
            self.name_valid = True
            return True
        except Exception, e:
            wiz.ui.project_name_errors.setText(str(e))
            self.name_valid = False
            return False

    def _setup_storage_widgets(self, project_paths_dict):
        # setup os info and ordering
        os_info = [
            # (dict key, label, current os)
            ("darwin", "Mac", sys.platform == "darwin"),
            ("linux2", "Linux", sys.platform.startswith("linux")),
            ("win32", "Windows", sys.platform == "win32"),
        ]

        # current os first, then alphabetically
        def os_key(element):
            # return a key that sorts the os'es properly
            (_, label, os_current) = element
            return (not os_current, label)
        os_info.sort(key=os_key)

        wiz = self.wizard()
        for storage in project_paths_dict:
            # each storage gets a group showing what paths will be created for that storage
            group = QtGui.QGroupBox(" %s " % storage.title())
            group.setStyleSheet("""
                QGroupBox {
                    border: 1px solid rgb(217, 217, 217);
                    border-radius: 3px;
                    margin-top: 0.5em;
                }

                QGroupBox::title {
                    font-size: 14px;
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px 0 3px;
                    color: rgb(55, 168, 225);
                }
            """)
            group_layout = QtGui.QGridLayout(group)
            row = 0
            for (key, label, _) in os_info:
                path = project_paths_dict[storage].get(key)
                if path:
                    group_layout.addWidget(QtGui.QLabel("<big>%s</big>" % label), row, 0, 1, 1)
                    path_widget = QtGui.QLabel()
                    self._storage_path_widgets.setdefault(storage, {})[key] = path_widget
                    group_layout.addWidget(path_widget, row, 1, 1, 1)
                    row += 1
            group_layout.setColumnStretch(1, 1)
            group_layout.setHorizontalSpacing(15)
            wiz.ui.project_contents_layout.addWidget(group)
            
            # Keep added widgets in order to remove them in case back button is used.
            self._widget_groups.append(group)

    def isComplete(self):
        return self.name_valid
