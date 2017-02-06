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
from sgtk.util import shotgun

from .base_page import BasePage


class StorageLocationsPage(BasePage):
    """ Page to collect the needed storages for the selected config. """
    _HELP_URL = BasePage._HELP_URL + "#Setting%20up%20a%20storage"

    def __init__(self, store_name, store_info, uri, parent=None):
        BasePage.__init__(self, parent)

        # initialize member variables
        self._uri = uri
        self._store_name = store_name
        self._store_info = store_info
        self._last_page = False

        # setup the UI
        layout = QtGui.QGridLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        self.setTitle("<p></p><font size=18>Define %s Storage</font><p></p>" % store_name.title())
        self.setSubTitle("&nbsp;")

        # setup the subtitle
        subtitle = QtGui.QLabel(self)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px;")
        subtitle.setText("""
            <p style="line-height: 130%%">
                Specify where you want Shotgun to store files on disk.<br/>
                If you use multiple operating systems, enter the equivalent path for each.<br/>
            </p>
        """)
        layout.addWidget(subtitle, 0, 0, 1, 4)

        # setup a label to describe the storage
        description = QtGui.QLabel(self)
        description.setWordWrap(True)
        description.setText(
            """
            <p style="line-height: 130%%">
                Storage description:<br/>
                %s
            </p>
        """ % (store_info["description"]))
        layout.addWidget(description, 1, 0, 1, 4)

        # add a spacer between storages
        spacer = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        layout.addItem(spacer, 2, 0, 1, 4)

        # Setup a group of line edits per storage
        os_specifics = [
            # (Label, info_key, current_os)
            ("Mac", "darwin", "/Path/On/Mac", sys.platform == "darwin"),
            ("Linux", "linux2", "/path/on/linux", sys.platform.startswith("linux")),
            ("Windows", "win32", "\\\\Path\\On\\Windows", sys.platform == "win32"),
        ]

        # current os first, then alphabetically
        def os_key(element):
            # return a key that sorts the os'es properly
            (os_display, _, _, os_current) = element
            return (not os_current, os_display)
        os_specifics.sort(key=os_key)

        self._store_path_widgets = {}
        for (i, (os_display, os_key, os_placeholder, os_current)) in enumerate(os_specifics):
            # setup the os widgets
            os_label = QtGui.QLabel("%s" % os_display, self)
            os_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
            os_path = QtGui.QLineEdit(self)
            os_path.setPlaceholderText(os_placeholder)
            os_path_locked = None

            # populate with existing paths
            if store_info[os_key]:
                os_path.setText(store_info[os_key])

            # don't allow editing data from Shotgun, too dangerous
            if store_info["defined_in_shotgun"] and store_info[os_key]:
                tooltip = ("There is already a Local Storage defined in your Shotgun Site Preferences "
                           "named \"%s\". In order to change these paths, you'll need to update this Local "
                           "Storage definition in your Shotgun Site Preferences." % store_name)
                os_path.setReadOnly(True)
                os_path.setEnabled(False)
                os_path.setToolTip(tooltip)

                os_path_locked = QtGui.QLabel(self)
                os_path_locked.setPixmap(QtGui.QPixmap(":/tk-framework-adminui/setup_project/icon_lock.png"))
                os_path_locked.setAlignment(QtCore.Qt.AlignVCenter)
                os_path_locked.setToolTip(tooltip)

                os_label.setToolTip(tooltip)

            # keep around the line edits for validation
            self._store_path_widgets[os_key] = os_path

            # only create the browse button for the current os if
            #  the storage is not in Shotgun or
            #  the storage is blank in Shotgun
            create_browse = os_current and (
                not store_info["defined_in_shotgun"] or
                (store_info["defined_in_shotgun"] and not store_info[os_key]))
            if create_browse:
                os_button = QtGui.QPushButton("Browse...", self)

                # connect the button to populate the os specific path
                def generate_on_browse_clicked(path_widget):
                    # generate the slot as a closure to capture the current widget
                    def ret():
                        storage_dir = QtGui.QFileDialog.getExistingDirectory(
                            self, "Choose storage root", None,
                            QtGui.QFileDialog.ShowDirsOnly |
                            QtGui.QFileDialog.DontConfirmOverwrite)
                        path_widget.setText(storage_dir)
                    return ret
                os_button.pressed.connect(generate_on_browse_clicked(os_path))

            # add the widgets to the layout
            layout.addWidget(os_label, 3+i, 0, 1, 1)
            if os_path_locked:
                layout.addWidget(os_path_locked, 3+i, 1, 1, 1)
            layout.addWidget(os_path, 3+i, 2, 1, 1)
            if create_browse:
                layout.addWidget(os_button, 3+i, 3, 1, 1)

        # add a spacer since
        spacer = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        layout.addItem(spacer, 6, 0, 1, 4)

        # setup a place to report errors
        self.storage_errors = QtGui.QLabel(self)
        self.storage_errors.setWordWrap(True)
        self.storage_errors.setStyleSheet("color: rgb(252, 98, 70);")
        self.storage_errors.setAlignment(QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        layout.addWidget(self.storage_errors, 7, 0, 1, 4)

    def set_next_page(self, page, last_page=False):
        """ Override which page comes next """
        BasePage.set_next_page(self, page)
        self._last_page = last_page

    def validatePage(self):
        # clear any errors
        self.storage_errors.setText("")

        # get the os key for the current platform
        current_os = sys.platform
        if current_os.startswith("linux"):
            current_os = "linux2"

        # gather the different kinds of operations we might have to do
        invalid = False
        not_on_disk = None
        update_in_shotgun = {}
        create_in_shotgun = {}
        invalid_in_shotgun = False

        # grab the path for the operating systems
        current_os_path = str(self._store_path_widgets[current_os].text())
        mac_path = str(self._store_path_widgets["darwin"].text())
        windows_path = str(self._store_path_widgets["win32"].text())
        linux_path = str(self._store_path_widgets["linux2"].text())

        if self._store_info["defined_in_shotgun"]:
            # see if any shotgun values have changed
            # only values that started blank were set to read/write
            for (os_path, os_key, sg_key) in [
                    (mac_path, "darwin", "mac_path"),
                    (windows_path, "win32", "windows_path"),
                    (linux_path, "linux2", "linux_path")]:
                if os_path and os_path != self._store_info[os_key]:
                    if not (os_key == current_os) or os.path.isabs(os_path):
                        # path is changed
                        # check that it is an absolute path for the current os
                        # if so, then update
                        update_in_shotgun[sg_key] = os_path
                    else:
                        # path is not valid, add it to the list of invalids
                        invalid = True

            # if there were changes, add them to the update list
            if update_in_shotgun:
                update_in_shotgun["code"] = self._store_name

            # special checks for current operating system
            if current_os_path and os.path.isabs(current_os_path):
                if not os.path.exists(current_os_path):
                    not_on_disk = current_os_path
            elif self._store_info[current_os] and current_os_path == self._store_info[current_os]:
                # path is invalid in Shotgun
                # (if it were changed and invalid it would be picked up above)
                invalid_in_shotgun = True
        else:
            # not in shotgun need to make sure the path is filled out and valid
            if not current_os_path or not os.path.isabs(current_os_path):
                invalid = True
            else:
                # valid path, add to the create list
                create_in_shotgun = {
                    "code": self._store_name,
                    "mac_path": mac_path,
                    "windows_path": windows_path,
                    "linux_path": linux_path,
                }

                # and see if we are going to have to create the path
                if not os.path.exists(current_os_path):
                    not_on_disk = current_os_path

        # if the current path is invalid in Shotgun, then we aren't going to be able to continue
        if invalid_in_shotgun:
            # display a message about the invalid paths
            message = "The path for the current os is invalid in Shotgun.  Please correct it in the " \
                "File Management section of your Shotgun preferences and then try setting up the " \
                "project again:\n\n%s" % current_os_path
            self.storage_errors.setText(message)
            return False

        # if local paths don't exist
        if not_on_disk:
            # try to create the directories
            old_umask = os.umask(0)
            try:
                os.makedirs(not_on_disk, 0777)
                self._store_info["exists_on_disk"] = True
            except Exception, e:
                # could not create all the directories, report and bail
                message = "Got the following errors creating the directory:\n%s" % str(e)
                QtGui.QMessageBox.critical(self, "Error creating directories.", message)
                return False
            finally:
                os.umask(old_umask)

        # report if invalid paths were entered
        if invalid:
            error = "All paths must be filled out with absolute paths."
            self.storage_errors.setText(error)
            return False

        # do create
        sg = shotgun.create_sg_connection()
        if create_in_shotgun:
            try:
                shotgun_store = sg.create("LocalStorage", create_in_shotgun)
                self._store_info["defined_in_shotgun"] = True
                self._store_info["shotgun_id"] = shotgun_store["id"]
                self._store_info["darwin"] = mac_path
                self._store_info["linux2"] = linux_path
                self._store_info["win32"] = windows_path
            except Exception, e:
                self.storage_errors.setText("Error creating Storage in Shotgun:\n%s" % str(e))
                return False

        # grab the ids for the local storages from Shotgun
        # NOTE: this is temporary until the store_info dictionary includes the id
        if update_in_shotgun:
            try:
                local_stores = sg.find("LocalStorage", [], fields=["code", "id"])
                local_store_map = dict([(s["code"], s["id"]) for s in local_stores])
                sg.update("LocalStorage", local_store_map[update_in_shotgun["code"]], update_in_shotgun)

                if "mac_path" in update_in_shotgun:
                    self._store_info["darwin"] = update_in_shotgun["mac_path"]
                if "linux_path" in update_in_shotgun:
                    self._store_info["linux2"] = update_in_shotgun["linux_path"]
                if "windows_path" in update_in_shotgun:
                    self._store_info["win32"] = update_in_shotgun["windows_path"]
            except Exception, e:
                self.storage_errors.setText("Error updating Storage in Shotgun:\n%s" % str(e))
                return False

        # if we made it here, then we should be all valid.  Try to set the config
        if self._last_page:
            try:
                wiz = self.wizard()
                wiz.core_wizard.set_config_uri(self._uri)
            except Exception, e:
                error = "Unknown error when setting the configuration uri:\n%s" % str(e)
                self.storage_errors.setText(error)
                return False

        # uri all set and all storages now valid
        return True
