# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
An app that shows information about the current work area.

"""

import sys
import os
import platform

from tank.platform import Application

class AboutTank(Application):
    
    def init_app(self):
        """
        Called as the application is being initialized
        """
        tk_multi_about = self.import_module("tk_multi_about")
        cb = lambda : tk_multi_about.show_dialog(self)
        self.engine.register_command("Work Area Info...", cb, {"type": "context_menu", "short_name": "work_area_info"})

    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return True

