# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
import unicodedata
import os
import sys
import threading

from tank.platform.qt import QtCore, QtGui
from tank.platform import restart
from .ui.dialog import Ui_Dialog

class AppDialog(QtGui.QWidget):

    
    def __init__(self, app):
        QtGui.QWidget.__init__(self)
        # set up the UI
        self.ui = Ui_Dialog() 
        self.ui.setupUi(self)
        
        self._app = app
        
        # set up the browsers
        self.ui.context_browser.set_app(self._app)
        self.ui.context_browser.set_label("Your Current Work Context")
        self.ui.context_browser.enable_search(False)        
        self.ui.context_browser.action_requested.connect( self.show_in_sg )
        
        self.ui.app_browser.set_app(self._app)
        self.ui.app_browser.set_label("Currently Running Apps")
        self.ui.app_browser.action_requested.connect( self.show_app_in_app_store )        

        self.ui.environment_browser.set_app(self._app)
        self.ui.environment_browser.set_label("The Current Environment")
        self.ui.environment_browser.enable_search(False)        
        self.ui.environment_browser.action_requested.connect( self.show_engine_in_app_store )
        
        self.ui.jump_to_fs.clicked.connect( self.show_in_fs )
        self.ui.support.clicked.connect( self.open_helpdesk )
        self.ui.reload_apps.clicked.connect( self.reload )
        self.ui.close.clicked.connect( self.close )

        # load data from shotgun
        self.setup_context_list()
        self.setup_apps_list()
        self.setup_environment_list()

        # When there is no file system locations, hide the "Jump to the File System" button.
        if not self._app.context.filesystem_locations:
            self.ui.jump_to_fs.setVisible(False)


    ########################################################################################
    # make sure we trap when the dialog is closed so that we can shut down 
    # our threads. Nuke does not do proper cleanup on exit.
    
    def closeEvent(self, event):        
        self.ui.context_browser.destroy()
        self.ui.app_browser.destroy()
        self.ui.environment_browser.destroy()
        # okay to close!
        event.accept()
        
        
    ########################################################################################
    # basic business logic        
                
    def setup_context_list(self): 
        self.ui.context_browser.clear()
        self.ui.context_browser.load({})
        
    def setup_apps_list(self): 
        self.ui.app_browser.clear()
        self.ui.app_browser.load({})

    def setup_environment_list(self): 
        self.ui.environment_browser.clear()
        self.ui.environment_browser.load({})

    def open_helpdesk(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("http://support.shotgunsoftware.com"))
    
    def reload(self):
        """
        Reload templates and restart engine.
        """
        restart()
    
    def show_in_fs(self):
        """
        Jump from context to FS
        """
        # launch one window for each location on disk
        paths = self._app.context.filesystem_locations
        for disk_location in paths:
                
            # get the setting        
            system = sys.platform
            
            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)
            
            exit_code = os.system(cmd)
            if exit_code != 0:
                self._app.log_error("Failed to launch '%s'!" % cmd)
        
        
    def show_in_sg(self):
        """
        Jump to shotgun
        """
        curr_selection = self.ui.context_browser.get_selected_item()
        if curr_selection is None:
            return
        
        data = curr_selection.sg_data
        
        # steps do not have detail pages in shotgun so omit those
        if data["type"] == "Step":
            return
        
        sg_url = "%s/detail/%s/%d" % (self._app.shotgun.base_url, data["type"], data["id"])        
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(sg_url))
        

    def show_app_in_app_store(self):
        """
        Jump to app store
        """
        curr_selection = self.ui.app_browser.get_selected_item()
        if curr_selection is None:
            return
        
        doc_url = curr_selection.data.get("documentation_url")
        if doc_url is None:
            QtGui.QMessageBox.critical(self, 
                                       "No Documentation found!",
                                       "Sorry, this app does not have any associated documentation!")
        else:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(doc_url))

    def show_engine_in_app_store(self):
        """
        Jump to app store
        """
        curr_selection = self.ui.environment_browser.get_selected_item()
        if curr_selection is None:
            return
        
        doc_url = curr_selection.data.get("documentation_url")
        if doc_url:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(doc_url))

        
