# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from .menu_generation import MenuGenerator
from .qt_parent_window import get_qt_parent_window

import sys
if sys.platform == "win32":
    from .win32 import find_windows

def define_qt_base():
    """
    Call out to tk-framework-softimageqt to define the qt base to use
    for the Softimage engine
    """
    import sgtk
    qt_fw = sgtk.platform.get_framework("tk-framework-softimageqt")
    return qt_fw.define_qt_base()