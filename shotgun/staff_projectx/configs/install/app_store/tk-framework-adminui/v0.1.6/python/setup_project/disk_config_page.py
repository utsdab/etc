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

from sgtk.platform.qt import QtGui

from .base_page import BasePage


class DiskConfigPage(BasePage):
    """ Page to base a configuration on a disk location. """
    _HELP_URL = BasePage._HELP_URL + "#Browsing%20for%20a%20configuration%20template"

    def setup_ui(self, page_id):
        BasePage.setup_ui(self, page_id)

        wiz = self.wizard()
        wiz.ui.disk_browse_button_dir.pressed.connect(self._on_browse_pressed)
        wiz.ui.disk_browse_button_zip.pressed.connect(self._on_browse_zip_pressed)

    def _on_browse_pressed(self):
        config_dir = QtGui.QFileDialog.getExistingDirectory(
            self, "Choose pipeline configuration directory", None,
            QtGui.QFileDialog.ShowDirsOnly |
            QtGui.QFileDialog.DontConfirmOverwrite |
            QtGui.QFileDialog.ReadOnly)
        self.setField("disk_path", config_dir)

    def _on_browse_zip_pressed(self):
        config_zip = QtGui.QFileDialog.getOpenFileName(
            self, "Choose pipeline configuration zip", None, "*.zip")
        # Unlike getExistingDirectory(), getOpenFileName() always returns a path with / separators. 
        # So we need to convert them for Windows since core expects the path to be a native one.
        zip_path = str(config_zip[0])
        self.setField("disk_path", zip_path.replace("/", os.path.sep))

    def validatePage(self):
        uri = self.field("disk_path")
        wiz = self.wizard()
        try:
            wiz.set_config_uri(uri)
            wiz.ui.disk_errors.setText("")
        except Exception, e:
            wiz.ui.disk_errors.setText(str(e))
            return False

        return True
