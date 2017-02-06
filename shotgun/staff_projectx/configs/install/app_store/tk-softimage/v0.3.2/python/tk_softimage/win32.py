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
Windows specific functionality
"""

import win32gui
import win32con
import win32process
import win32api

import ctypes
from ctypes import wintypes

def safe_get_window_text(hwnd):
    """
    Safely get the window text (title) of a specified window
    :param hwnd: window handle to get the text of
    :returns: window title if found
    """
    title = ""
    try:
        # Note - we use SendMessageTimeout instead of GetWindowText as the later 
        # will hang if the target window isn't processing messages for some reason
        buffer_sz = 1024
        buffer = win32gui.PyMakeBuffer(buffer_sz)
        _,result = win32gui.SendMessageTimeout(hwnd, win32con.WM_GETTEXT, buffer_sz, buffer, win32con.SMTO_ABORTIFHUNG | win32con.SMTO_BLOCK, 100)
        if result != 0:
            title = buffer[:result]
    except:
        pass
    return title
    
def find_windows(thread_id = None, process_id = None, parent_hwnd = None, class_name = None, window_text = None, stop_if_found = True):
    """
    Find top level windows matching certain criteria
    :param process_id: only match windows that belong to this process id if specified
    :param class_name: only match windows that match this class name if specified
    :param window_text: only match windows that match this window text if specified
    :param stop_if_found: stop when find a match
    :returns: list of window handles found by search
    """
    found_hwnds = []

    # sub-function used to actually enumerate the windows in EnumWindows
    def enum_windows_proc(hwnd, lparam):
        # print "Window name: %s" % safe_get_window_text(hwnd)
        # print "Window class: %s" % win32gui.GetClassName(hwnd)
        # print "Window process id: %s" % win32process.GetWindowThreadProcessId(hwnd)[1]

        # try to match process id:
        if process_id != None:
            _,win_process_id = win32process.GetWindowThreadProcessId(hwnd)
            if win_process_id != process_id:
                return True    
    
        # try to match class name:
        if class_name != None and (win32gui.GetClassName(hwnd) != class_name):
            return True
       
        # try to match window text:
        matches_window_text = True
        if window_text != None and (window_text not in safe_get_window_text(hwnd)):
            return True
        
        # found a match    
        found_hwnds.append(hwnd)
        
        return not stop_if_found
            
    # enumerate all top-level windows:
    try:
        if parent_hwnd != None:
            win32gui.EnumChildWindows(parent_hwnd, enum_windows_proc, None)
        elif thread_id != None:
            win32gui.EnumThreadWindows(thread_id, enum_windows_proc, None)
        else:    
            win32gui.EnumWindows(enum_windows_proc, None)
    except:
        # stupid api!
        pass
    
    return found_hwnds

def has_children(hwnd):
    """
    Determine if the specified HWND has any 
    child windows
    """
    def enum_window_callback(hwnd, windows):
        windows.append(hwnd)
        # stop enumeration
        return False
        
    child_windows = []
    try:
        win32gui.EnumChildWindows(hwnd, enum_window_callback, child_windows)
    except:
        pass

    return bool(child_windows)

def qwidget_winid_to_hwnd(id):
    """
    Convert the winid for a qtwidget to a HWND
    :param id: qtwidget winid to convert
    :returns: window handle
    """
    # Setup arguments and return types
    ctypes.pythonapi.PyCObject_AsVoidPtr.restype = ctypes.c_void_p
    ctypes.pythonapi.PyCObject_AsVoidPtr.argtypes = [ ctypes.py_object ]
 
    # Convert PyCObject to a void pointer
    hwnd = ctypes.pythonapi.PyCObject_AsVoidPtr(id)
    
    return hwnd

