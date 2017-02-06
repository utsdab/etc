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


class SetupTypePage(BasePage):
    """ Page to choose what configuration type to use. """
    STANDARD_ID = 0
    PROJECT_ID = 1
    GITHUB_ID = 2
    DISK_ID = 3

    def __init__(self, parent=None):
        BasePage.__init__(self, parent)
        self._disk_page_id = None
        self._github_page_id = None
        self._project_page_id = None
        self._default_configs_page_id = None

    def setup_ui(self, page_id):
        BasePage.setup_ui(self, page_id)

        # Setup buttongroup by hand since in PySide it breaks the ui compilation
        wiz = self.wizard()
        self._config_type_button_group = QtGui.QButtonGroup(self)
        self._config_type_button_group.addButton(wiz.ui.select_standard, self.STANDARD_ID)
        self._config_type_button_group.addButton(wiz.ui.select_project, self.PROJECT_ID)
        self._config_type_button_group.addButton(wiz.ui.select_github, self.GITHUB_ID)
        self._config_type_button_group.addButton(wiz.ui.select_disk, self.DISK_ID)

    def set_project_page(self, page):
        """ Set the page to switch to if project is selected. """
        self._project_page_id = page.page_id()

    def set_github_page(self, page):
        """ Set the page to switch to if github url is selected. """
        self._github_page_id = page.page_id()

    def set_disk_page(self, page):
        """ Set the page to switch to if disk location is selected. """
        self._disk_page_id = page.page_id()

    def set_default_configs_page(self, page):
        """ Set the page to switch to if default config is selected. """
        self._default_configs_page_id = page.page_id()

    def nextId(self):
        # return the appropriate id for the current selection
        selection = self._config_type_button_group.checkedId()
        if (selection == 0) and self._default_configs_page_id is not None:
            return self._default_configs_page_id
        if (selection == 1) and self._project_page_id is not None:
            return self._project_page_id
        elif (selection == 2) and self._github_page_id is not None:
            return self._github_page_id
        elif (selection == 3) and self._disk_page_id is not None:
            return self._disk_page_id

        return BasePage.nextId(self)
