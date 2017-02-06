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
from sgtk import TankError

import traceback

class BasePage(QtGui.QWizardPage):
    """ Base page for all Shotgun pages to inherit from. """
    # by default return the general setting up your project page
    _HELP_URL = "https://support.shotgunsoftware.com/entries/95442748"

    def __init__(self, parent=None):
        """ Constructor """
        QtGui.QWizardPage.__init__(self, parent)
        self._page_id = None
        self._next_page_id = None
        self._error_field = None

    def setup_ui(self, page_id, error_field=None):
        """ 
        Setup page UI after the Wizard's UI has been setup from the uic. 
        :param page_id: Page id for current page.
        :param error_field: QLabel object to use to display error messages. 
                            These messages may be one-liners as well as full call stacks.
        """
        self._page_id = page_id
        self._error_field = error_field

    def page_id(self):
        """ Return the cached id of this page """
        return self._page_id

    def set_next_page(self, page):
        """ Override which page comes next """
        self._next_page_id = page.page_id()

    def nextId(self):
        """ Enhanced logic for non-linear wizards """
        if self._next_page_id is None:
            return QtGui.QWizardPage.nextId(self)

        return self._next_page_id

    def help_requested(self):
        if self._HELP_URL:
            QtGui.QDesktopServices.openUrl(self._HELP_URL)

    def validatePage(self):
        """
        Validate the current page.

        The idea of having this in BasePage is that whatever the last page is 
        will be the one calling pre_setup_validation.
        """
        state = True

        try:
            # Validate 
            if self.isCommitPage():
                wiz = self.wizard()
                wiz.core_wizard.pre_setup_validation()
        except TankError, e:
            if self._error_field:
                self._error_field.setText(str(e))
            state = False
        except Exception, e:
            if self._error_field:
                self._error_field.setText(traceback.format_exc())
            state = False

        return state
