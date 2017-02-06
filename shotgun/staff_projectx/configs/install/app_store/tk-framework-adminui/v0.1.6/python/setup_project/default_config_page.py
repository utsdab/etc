# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtGui

from .base_page import BasePage
from .wait_screen import WaitScreen


class DefaultConfigPage(BasePage):
    """ Page to choose which default configuration to use. """
    _HELP_URL = BasePage._HELP_URL + "#Default%20configuration%20templates"

    DEFAULT_ID = 0
    MULTIROOT_ID = 1
    GAMES_ID = 2
    FLAME_ID = 3

    SELECTION_ID_MAP = {
        DEFAULT_ID: "tk-config-default",
        MULTIROOT_ID: "tk-config-multiroot",
        GAMES_ID: "tk-config-games",
        FLAME_ID: "tk-config-flame",
    }

    def __init__(self, parent=None):
        BasePage.__init__(self, parent)

    def setup_ui(self, page_id):
        BasePage.setup_ui(self, page_id)

        # Setup buttongroup by hand since in PySide it breaks the ui compilation
        wiz = self.wizard()
        self._config_button_group = QtGui.QButtonGroup(self)
        self._config_button_group.addButton(wiz.ui.select_default_config, self.DEFAULT_ID)
        self._config_button_group.addButton(wiz.ui.select_multiroot_config, self.MULTIROOT_ID)
        self._config_button_group.addButton(wiz.ui.select_games_config, self.GAMES_ID)
        self._config_button_group.addButton(wiz.ui.select_flame_config, self.FLAME_ID)

    def validatePage(self):
        selected_id = self._config_button_group.checkedId()
        uri = self.SELECTION_ID_MAP[selected_id]
        wiz = self.wizard()

        wait = WaitScreen("Downloading Config,", "hold on...", parent=self)
        wait.show()
        QtGui.QApplication.instance().processEvents()
        try:
            wiz.set_config_uri(uri)
            wiz.ui.github_errors.setText("")
        except Exception, e:
            wiz.ui.default_configs_errors.setText(str(e))
            return False
        finally:
            wait.hide()

        return True
