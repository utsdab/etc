# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import random

from sgtk.platform.qt import QtCore

from .base_page import BasePage
from .wait_screen import WaitScreen
from ..ui import resources_rc


class GithubConfigPage(BasePage):
    """ Page to base a configuration on a github repo. """
    _HELP_URL = BasePage._HELP_URL + "#Using%20a%20configuration%20template%20from%20git"

    def initializePage(self):
        # pick a random octocat
        cats = []
        dir_iter = QtCore.QDirIterator(
            ":tk-framework-adminui/setup_project/octocats", QtCore.QDirIterator.Subdirectories)

        cat = dir_iter.next()
        while cat:
            cats.append(cat)
            cat = dir_iter.next()

        if cats:
            selected = random.choice(cats)
            wiz = self.wizard()
            wiz.ui.octocat.setPixmap(selected)

    def validatePage(self):
        wiz = self.wizard()
        uri = self.field("github_url")
        if not uri.endswith(".git"):
            wiz.ui.github_errors.setText("Error, the url does not end in '.git'")
            return False

        wait = WaitScreen("Downloading Config,", "hold on...", parent=self)
        wait.show()
        try:
            wiz.set_config_uri(uri)
            wiz.ui.github_errors.setText("")
        except Exception, e:
            wiz.ui.github_errors.setText(str(e))
            return False
        finally:
            wait.hide()

        return True
