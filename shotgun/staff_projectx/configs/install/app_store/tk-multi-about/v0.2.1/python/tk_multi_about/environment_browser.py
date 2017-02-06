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

class EnvironmentBrowserWidget(browser_widget.BrowserWidget):

    
    def __init__(self, parent=None):
        browser_widget.BrowserWidget.__init__(self, parent)
    
    def get_data(self, data):
    
        engine = self._app.engine
            
        data = {}
        
        data["engine"] = {"name": engine.display_name,
                          "version": engine.version,
                          "documentation_url": engine.documentation_url,
                          "description": engine.description
                          }
        
        data["environment"] = {"name": engine.environment.get("name"),
                               "disk_location": engine.environment.get("disk_location"),
                               "description": engine.environment.get("description")
                               }
        
        return data
        

    def process_result(self, result):

        d = result["engine"]

        i = self.add_item(browser_widget.ListItem)
        details = []
        details.append("<b>Engine: %s</b>" % d.get("name"))
        details.append("Version: %s" % d.get("version"))
        details.append("Description: %s" % d.get("description"))    
        i.set_details("<br>".join(details))
        i.data = d
        i.setToolTip("Double click for documentation.")
        i.set_thumbnail(":/res/tank_app_logo.png")

        
        d = result["environment"]

        i = self.add_item(browser_widget.ListItem)
        details = []
        details.append("<b>Environment: %s</b>" % d.get("name"))
        details.append("Path: %s" % d.get("disk_location"))
        details.append("Description: %s" % d.get("description"))    
        i.set_details("<br>".join(details))
        i.data = d
        i.set_thumbnail(":/res/tank_env_logo.png")
            