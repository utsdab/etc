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
import os
import sys
import datetime
import threading 


from tank.platform.qt import QtCore, QtGui

browser_widget = tank.platform.import_framework("tk-framework-widget", "browser_widget")

class AppBrowserWidget(browser_widget.BrowserWidget):

    
    def __init__(self, parent=None):
        browser_widget.BrowserWidget.__init__(self, parent)
    
    def get_data(self, data):
    
        data = {}
        for app in self._app.engine.apps.values():
            data[app.name] = {"display_name": app.display_name,
                              "version": app.version,
                              "documentation_url": app.documentation_url,
                              "description": app.description
                              }
        return data
            

    def process_result(self, result):
        
        for app in result.values():
        
            i = self.add_item(browser_widget.ListItem)
            details = []
            details.append("<b>%s</b>" % app.get("display_name"))
            details.append("Version: %s" % app.get("version"))
            details.append("Description: %s" % app.get("description"))    
            i.set_details("<br>".join(details))
            i.data = app
            i.setToolTip("Double click for documentation.")
            i.set_thumbnail(":/res/tank_app_logo.png")
            