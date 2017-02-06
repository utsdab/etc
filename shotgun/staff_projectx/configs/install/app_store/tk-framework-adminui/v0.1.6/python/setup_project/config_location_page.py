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
from sgtk.platform.qt import QtCore

from .base_page import BasePage


class ConfigLocationPage(BasePage):
    """ Page to specify the location for the configuration. """
    _HELP_URL = BasePage._HELP_URL + "#Selecting%20a%20configuration%20location"

    def __init__(self, parent=None):
        BasePage.__init__(self, parent)
        self._path_widget = None

    def setup_ui(self, page_id):
        wiz = self.wizard()

        BasePage.setup_ui(self, page_id, wiz.ui.config_location_errors)

        # update the layout of the os specific widgets
        ui = wiz.ui
        os_widgets = [
            (ui.linux_label, ui.linux_path, ui.linux_browse, sys.platform.startswith("linux")),
            (ui.mac_label, ui.mac_path, ui.mac_browse, sys.platform == "darwin"),
            (ui.windows_label, ui.windows_path, ui.windows_browse, sys.platform == "win32"),
        ]

        # current os first, then alphabetically
        def os_key(element):
            # return a key that sorts the os'es properly
            (label, _, _, os_current) = element
            return (not os_current, label.text())
        os_widgets.sort(key=os_key)

        # remove the widgets from the layout
        for (label, path, browse, _) in os_widgets:
            self.layout().removeWidget(label)
            self.layout().removeWidget(path)
            self.layout().removeWidget(browse)

        # add them back in
        offset = 2
        for (row, (label, path, browse, os_current)) in enumerate(os_widgets):
            self.layout().addWidget(label, row+offset, 0, 1, 1)
            self.layout().addWidget(path, row+offset, 2, 1, 1)
            if os_current:
                # current os gets browse setup and we track the path widget
                self.layout().addWidget(browse, row+offset, 3, 1, 1)
                browse.pressed.connect(self._on_browse_pressed)
                self._path_widget = path
            else:
                # hide the browse button on all other os'es
                browse.hide()

    def _on_browse_pressed(self):
        config_dir = QtGui.QFileDialog.getExistingDirectory(
            self, "Choose configuration", None,
            QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontConfirmOverwrite)
        self._path_widget.setText(config_dir)

    def initializePage(self):
        # setup the default locations
        # this must be done in initializePage since the answers depend on previous field values
        wiz = self.wizard()
        default_locations = wiz.core_wizard.get_default_configuration_location()
        self.wizard().ui.linux_path.setText(default_locations["linux2"])
        self.wizard().ui.windows_path.setText(default_locations["win32"])
        self.wizard().ui.mac_path.setText(default_locations["darwin"])

        self._path_widget.setFocus(QtCore.Qt.OtherFocusReason)

    def validatePage(self):
        # grab the os paths
        macosx_path = self.field("config_path_mac")
        linux_path = self.field("config_path_linux")
        windows_path = self.field("config_path_win")

        if sys.platform == "darwin":
            current_os_path = macosx_path
        elif sys.platform == "win32":
            current_os_path = windows_path
        elif sys.platform.startswith("linux2"):
            current_os_path = linux_path

        # check if the path for the current os passes basic validation
        wiz = self.wizard()
        if not current_os_path or not os.path.isabs(current_os_path):
            wiz.ui.config_location_errors.setText("Path must be an absolute path.")
            return False

        # create the path if it does not exist
        if not os.path.exists(current_os_path):
            old_umask = os.umask(0)
            try:
                os.makedirs(current_os_path, 0777)
            except Exception, e:
                # could not create the directories, report and bail
                message = "Got the following error creating the directory:\n %s" % str(e)
                QtGui.QMessageBox.critical(self, "Error creating directories.", message)
                return False
            finally:
                os.umask(old_umask)

        # pass the paths to the wizard and make sure they are ok
        try:
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            wiz.core_wizard.validate_configuration_location(linux_path, windows_path, macosx_path)
            wiz.core_wizard.set_configuration_location(linux_path, windows_path, macosx_path)
            wiz.core_wizard.set_default_core()
            wiz.ui.config_location_errors.setText("")
        except Exception, e:
            wiz.ui.config_location_errors.setText(str(e))
            return False
        finally:
            QtGui.QApplication.restoreOverrideCursor()

        # Previous validation code should be ran first as it setup necessary variables in core_wizard for
        # pre-commit validation.
        if not BasePage.validatePage(self): 
            return False

        return True
