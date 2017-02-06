# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import logging

from sgtk.platform.qt import QtGui
from sgtk.platform.qt import QtCore

from ..ui import setup_project
from .emitting_handler import EmittingHandler
from .storage_locations_page import StorageLocationsPage

import sgtk


class SetupProjectWizard(QtGui.QWizard):
    """
    A GUI wizard to setup a project for toolkit.

    This wraps the setup_project core command.
    """
    def __init__(self, project, parent=None):
        QtGui.QWizard.__init__(self, parent)

        # Disable Close button. Note that on mac, need to disable minimize 
        # button also to do this (but maximize can stay). 
        self.setWindowFlags(QtCore.Qt.Tool | 
                            QtCore.Qt.CustomizeWindowHint | 
                            QtCore.Qt.WindowTitleHint | 
                            QtCore.Qt.WindowMaximizeButtonHint)

        # Set stylesheet modification for this wizard
        self.setStyleSheet("QLineEdit:Disabled {background-color: rgb(60, 60, 60); color: rgb(128, 128, 128);}")

        # setup the command wizard from core
        wizard_factory = sgtk.get_command("setup_project_factory")

        # initialize storage setup pages
        self._storage_location_page_ids = []

        # setup logging
        self._logger = logging.getLogger("tk-framework-adminui.setup_project")
        self._handler = EmittingHandler()
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(self._handler)
        wizard_factory.set_logger(self._logger)

        # run the factory to grab the wizard
        self.core_wizard = wizard_factory.execute({})
        self.core_wizard.set_project(project["id"])

        # setup the GUI
        self.ui = setup_project.Ui_Wizard()
        self.ui.setupUi(self)

        # hook up logging
        self._handler.connect(self.ui.progress_page.append_log_message)

        # hook up help handling
        self.helpRequested.connect(self._on_help_requested)

        # Setup fields
        self.ui.github_config_page.registerField("github_url*", self.ui.github_url)
        self.ui.disk_config_page.registerField("disk_path*", self.ui.path)
        self.ui.project_name_page.registerField("project_name*", self.ui.project_name)
        self.ui.config_location_page.registerField("config_path_mac", self.ui.mac_path)
        self.ui.config_location_page.registerField("config_path_win", self.ui.windows_path)
        self.ui.config_location_page.registerField("config_path_linux", self.ui.linux_path)

        # Let each page set itself up
        for page_id in self.pageIds():
            page = self.page(page_id)
            if hasattr(page, "setup_ui"):
                self.page(page_id).setup_ui(page_id)

        # Setup Page Order
        self.ui.setup_type_page.set_default_configs_page(self.ui.default_configs_page)
        self.ui.setup_type_page.set_project_page(self.ui.project_config_page)
        self.ui.setup_type_page.set_github_page(self.ui.github_config_page)
        self.ui.setup_type_page.set_disk_page(self.ui.disk_config_page)

        self.ui.project_name_page.set_next_page(self.ui.config_location_page)
        self.ui.config_location_page.set_next_page(self.ui.progress_page)

        self.ui.config_location_page.setCommitPage(True)
        self.ui.summary_page.setFinalPage(True)

        # Override button formatting
        self.setButtonText(self.NextButton, "Continue")
        self.setButtonText(self.BackButton, "Back")
        self.setButtonText(self.FinishButton, "Done")
        self.setButtonText(self.CommitButton, "Run Setup")
        self.button(self.NextButton).setStyleSheet("background-color: rgb(16, 148,223);")
        self.button(self.FinishButton).setStyleSheet("background-color: rgb(16, 148,223);")
        self.button(self.CommitButton).setStyleSheet("background-color: rgb(16, 148,223);")

    def closeEvent(self, event):
        """
        Disables Alt-F4 on windows and prevents user from cancelling mid-operation and
        leaving the configuration in an un-recoverable state.
        """
        event.ignore()

    def _on_help_requested(self):
        # forward help request to current page
        page = self.currentPage()
        page.help_requested()

    def _is_store_valid(self, store_info):
        """ returns True if the store should be valid.  False otherwise """
        return store_info["exists_on_disk"] and store_info["defined_in_shotgun"]

    def set_config_uri(self, uri):
        """ set the config uri and adjust the state of the wizard to reflect needed pages """
        # clear the current storage pages
        for storage_page_id in self._storage_location_page_ids:
            self.removePage(storage_page_id)
        self._storage_location_page_ids = []

        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            # validate the uri and get the required storages
            # let any exceptions propagate up to the calling page to be handled
            storage_info = self.core_wizard.validate_config_uri(uri)
            for (store_name, store_info) in storage_info.iteritems():
                if not self._is_store_valid(store_info):
                    # storage is not available, show the page for it
                    page = StorageLocationsPage(store_name, store_info, uri)
                    page_id = self.addPage(page)
                    self._storage_location_page_ids.append(page_id)
                    page.setup_ui(page_id)

                    # set the page flow if this is not the first page
                    if len(self._storage_location_page_ids) > 1:
                        previous_page = self.page(self._storage_location_page_ids[-2])
                        previous_page.set_next_page(page, last_page=False)

            current_page = self.currentPage()
            if self._storage_location_page_ids:
                # have storage pages
                # let the last one know to set the uri on exit
                last_page = self.page(self._storage_location_page_ids[-1])
                last_page.set_next_page(self.ui.project_name_page, last_page=True)

                # set the first storage page as the next page
                first_page = self.page(self._storage_location_page_ids[0])
                current_page.set_next_page(first_page)
            else:
                # no storage pages set the right next page
                current_page.set_next_page(self.ui.project_name_page)

                # actually set the uri
                self.core_wizard.set_config_uri(uri)
        finally:
            QtGui.QApplication.restoreOverrideCursor()
