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
Implement a proxy parent window for all other Qt windows
"""

import sys

import win32com.client
Application = win32com.client.Dispatch('XSI.Application').Application

_QT_PARENT_TITLE = "Shotgun Pipeline Toolkit Qt Parent Window"

def get_qt_parent_window():
    """
    Get the parent QtWidget - all sgtk dialogs will be parented
    to this.  This will persist across engine restarts as it is
    held onto by the QApplication
    """
    global _QT_PARENT_TITLE
    
    # first, look to see if a proxy parent already exists:
    from sgtk.platform.qt import QtGui
    for widget in QtGui.QApplication.topLevelWidgets():
        if widget.windowTitle() == _QT_PARENT_TITLE:
            return widget

    # didn't find so lets create it:
    return _create_qt_parent_proxy()
    

def _create_qt_parent_proxy():
    """
    """
    import sgtk
    sgtk.platform.current_engine().log_debug("Creating Qt parent window proxy")
    
    global _QT_PARENT_TITLE
    
    from sgtk.platform.qt import QtGui, QtCore
    proxy_win = QtGui.QWidget()
    proxy_win.setWindowTitle(_QT_PARENT_TITLE) 
    
    if sys.platform == "win32":
        # on windows, we can parent directly to the application:
        
        # get the main window HWND
        import win32api, win32con, win32gui
        from .win32 import find_windows, qwidget_winid_to_hwnd
        found_hwnds = find_windows(thread_id = win32api.GetCurrentThreadId(), window_text = "Autodesk Softimage", stop_if_found=False)
        if len(found_hwnds) != 1:
            return
        si_hwnd = found_hwnds[0]

        # convert QWidget winId() to hwnd:
        proxy_win_hwnd = qwidget_winid_to_hwnd(proxy_win.winId())
        
        # set up the window style
        win_ex_style = win32gui.GetWindowLong(proxy_win_hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(proxy_win_hwnd, win32con.GWL_EXSTYLE, win_ex_style | win32con.WS_EX_NOPARENTNOTIFY)
        win32gui.SetWindowLong(proxy_win_hwnd, win32con.GWL_STYLE, win32con.WS_CHILD)
        
        # finally, parent to application window:
        win32gui.SetParent(proxy_win_hwnd, si_hwnd)
    else:
        # not able to parent directly on other os so just set to stay on top:
        proxy_win.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    # debug to prove that the window is actually parented!
    # proxy_win.show()

    return proxy_win