# Copyright (c) <2011>, Steven Caron <steven@steven-caron.com>
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Shotgun Note

This is a cut-down, modified version of the original that just maps
Softimage KeyUp & KeyDown events to the equivelant QtKeyEvent in Qt.

Additionally it uses the qt module from sgtk.platform.qt rather than
directly importing PySide/PyQT
"""

import sys
import win32com
from win32com.client import constants

def XSILoadPlugin( in_reg ):
    """
    Plug-in Load
    """    
    in_reg.Author = "Shotgun Software"
    in_reg.Name = "Shotgun Qt Keyboard Event Handlers"
    in_reg.Major = 1
    in_reg.Minor = 0

    """
    import sys
    path = in_reg.OriginPath
    if path not in sys.path:
        sys.path.append( path )
    """
    
    # register Shotgun specific events - this avoids possible
    # conflict if PyQtForSoftimage is also loaded!
    in_reg.RegisterEvent( "Shotgun Qt Events KeyDown", constants.siOnKeyDown )
    in_reg.RegisterEvent( "Shotgun Qt Events KeyUp", constants.siOnKeyUp )
    
    # also, register a timer event to ensure the Qt event loop is
    # processed at some stage!
    #
    # The effect of not processing events frequently is more noticeable on
    # Linux whilst processing too frequently can result in odd behaviour on
    # Windows, hence the different frequencies!
    timer_frequency = 1000
    if sys.platform == "win32":
        timer_frequency = 1000    
    elif sys.platform == "linux2":
        timer_frequency = 20
    
    in_reg.RegisterTimerEvent("Shotgun Qt Event Loop", timer_frequency, 0)
    
    return True

def XSIUnloadPlugin( in_reg ):
    """
    Plug-in Unload
    """
    Application.LogMessage( in_reg.Name + " has been unloaded.",constants.siVerbose)
    return True

#########################################################################################################################
def ShotgunQtEventLoop_OnEvent(in_ctxt):
    """
    Process QApplication events in a Softimage
    timer event just to be on the safe side!
    """
    try:
        import sgtk
        from sgtk.platform.qt import QtGui
        QtGui.QApplication.processEvents()
        QtGui.QApplication.sendPostedEvents(None, 0)
        #QtGui.QApplication.flush()
        #Application.Desktop.RedrawUI()
    except:
        pass

def ShotgunQtEventsKeyDown_OnEvent( in_ctxt ):
    """
    Block XSI keys from processing, pass along to Qt
    """
    if _is_qt_widget_focused():
        # process the key
        _consume_key( in_ctxt, True )

        # Block the Signal from XSI
        in_ctxt.SetAttribute( 'Consumed', True )

    return True

def ShotgunQtEventsKeyUp_OnEvent( in_ctxt ):
    """
    Block XSI keys from processing, pass along to Qt
    """
    if _is_qt_widget_focused():
        # process the key
        _consume_key( in_ctxt, False )

        # Block the Signal from XSI
        in_ctxt.SetAttribute( 'Consumed', True )

    return True

_SI_TO_QT_KEY_MAP = None
def _get_key_map():
    """
    Return the key map - fill it out if this is the first 
    time it's been requested!
    """
    global _SI_TO_QT_KEY_MAP
    if _SI_TO_QT_KEY_MAP == None:
        from sgtk.platform.qt import QtCore
        _SI_TO_QT_KEY_MAP = {
            # key: ( Qt::Key,           ascii,  modifiers )
        
              8: ( QtCore.Qt.Key_Backspace,    '',     None ),
              9: ( QtCore.Qt.Key_Tab,          '\t',   None ),
             13: ( QtCore.Qt.Key_Enter,        '\n',   None ),
             16: ( QtCore.Qt.Key_Shift,        '',     None ),
             17: ( QtCore.Qt.Key_Control,      '',     None ),
             18: ( QtCore.Qt.Key_Alt,          '',     None ),
             19: ( QtCore.Qt.Key_Pause,        '',     None ),
             20: ( QtCore.Qt.Key_CapsLock,     '',     None ),
             27: ( QtCore.Qt.Key_Escape,       '',     None ),
             32: ( QtCore.Qt.Key_Space,        ' ',    None ),
             33: ( QtCore.Qt.Key_PageUp,       '',     None ),
             34: ( QtCore.Qt.Key_PageDown,     '',     None ),
             35: ( QtCore.Qt.Key_End,          '',     None ),
             36: ( QtCore.Qt.Key_Home,         '',     None ),
             37: ( QtCore.Qt.Key_Left,         '',     None ),
             38: ( QtCore.Qt.Key_Up,           '',     None ),
             39: ( QtCore.Qt.Key_Right,        '',     None ),
             40: ( QtCore.Qt.Key_Down,         '',     None ),
             44: ( QtCore.Qt.Key_SysReq,       '',     None ),
             45: ( QtCore.Qt.Key_Insert,       '',     None ),
             46: ( QtCore.Qt.Key_Delete,       '',     None ),
             48: ( QtCore.Qt.Key_0,            '0',    None ),
             49: ( QtCore.Qt.Key_1,            '1',    None ),
             50: ( QtCore.Qt.Key_2,            '2',    None ),
             51: ( QtCore.Qt.Key_3,            '3',    None ),
             52: ( QtCore.Qt.Key_4,            '4',    None ),
             53: ( QtCore.Qt.Key_5,            '5',    None ),
             54: ( QtCore.Qt.Key_6,            '6',    None ),
             55: ( QtCore.Qt.Key_7,            '7',    None ),
             56: ( QtCore.Qt.Key_8,            '8',    None ),
             57: ( QtCore.Qt.Key_9,            '9',    None ),
             65: ( QtCore.Qt.Key_A,            'a',    None ),
             66: ( QtCore.Qt.Key_B,            'b',    None ),
             67: ( QtCore.Qt.Key_C,            'c',    None ),
             68: ( QtCore.Qt.Key_D,            'd',    None ),
             69: ( QtCore.Qt.Key_E,            'e',    None ),
             70: ( QtCore.Qt.Key_F,            'f',    None ),
             71: ( QtCore.Qt.Key_G,            'g',    None ),
             72: ( QtCore.Qt.Key_H,            'h',    None ),
             73: ( QtCore.Qt.Key_I,            'i',    None ),
             74: ( QtCore.Qt.Key_J,            'j',    None ),
             75: ( QtCore.Qt.Key_K,            'k',    None ),
             76: ( QtCore.Qt.Key_L,            'l',    None ),
             77: ( QtCore.Qt.Key_M,            'm',    None ),
             78: ( QtCore.Qt.Key_N,            'n',    None ),
             79: ( QtCore.Qt.Key_O,            'o',    None ),
             80: ( QtCore.Qt.Key_P,            'p',    None ),
             81: ( QtCore.Qt.Key_Q,            'q',    None ),
             82: ( QtCore.Qt.Key_R,            'r',    None ),
             83: ( QtCore.Qt.Key_S,            's',    None ),
             84: ( QtCore.Qt.Key_T,            't',    None ),
             85: ( QtCore.Qt.Key_U,            'u',    None ),
             86: ( QtCore.Qt.Key_V,            'v',    None ),
             87: ( QtCore.Qt.Key_W,            'w',    None ),
             88: ( QtCore.Qt.Key_X,            'x',    None ),
             89: ( QtCore.Qt.Key_Y,            'y',    None ),
             90: ( QtCore.Qt.Key_Z,            'z',    None ),
             93: ( QtCore.Qt.Key_Print,        '',     None ),
             96: ( QtCore.Qt.Key_0,            '0',    QtCore.Qt.KeypadModifier ),
             97: ( QtCore.Qt.Key_1,            '1',    QtCore.Qt.KeypadModifier ),
             98: ( QtCore.Qt.Key_2,            '2',    QtCore.Qt.KeypadModifier ),
             99: ( QtCore.Qt.Key_3,            '3',    QtCore.Qt.KeypadModifier ),
            100: ( QtCore.Qt.Key_4,            '4',    QtCore.Qt.KeypadModifier ),
            101: ( QtCore.Qt.Key_5,            '5',    QtCore.Qt.KeypadModifier ),
            102: ( QtCore.Qt.Key_5,            '6',    QtCore.Qt.KeypadModifier ),
            103: ( QtCore.Qt.Key_5,            '7',    QtCore.Qt.KeypadModifier ),
            104: ( QtCore.Qt.Key_5,            '8',    QtCore.Qt.KeypadModifier ),
            105: ( QtCore.Qt.Key_5,            '9',    QtCore.Qt.KeypadModifier ),
            106: ( QtCore.Qt.Key_Asterisk,     '*',    QtCore.Qt.KeypadModifier ),
            107: ( QtCore.Qt.Key_Plus,         '+',    QtCore.Qt.KeypadModifier ),
            109: ( QtCore.Qt.Key_Minus,        '-',    QtCore.Qt.KeypadModifier ),
            110: ( QtCore.Qt.Key_Period,       '.',    QtCore.Qt.KeypadModifier ),
            111: ( QtCore.Qt.Key_Slash,        '/',    QtCore.Qt.KeypadModifier ),
            112: ( QtCore.Qt.Key_F1,           '',     None ),
            113: ( QtCore.Qt.Key_F2,           '',     None ),
            114: ( QtCore.Qt.Key_F3,           '',     None ),
            115: ( QtCore.Qt.Key_F4,           '',     None ),
            116: ( QtCore.Qt.Key_F5,           '',     None ),
            117: ( QtCore.Qt.Key_F6,           '',     None ),
            118: ( QtCore.Qt.Key_F7,           '',     None ),
            119: ( QtCore.Qt.Key_F8,           '',     None ),
            120: ( QtCore.Qt.Key_F9,           '',     None ),
            121: ( QtCore.Qt.Key_F10,          '',     None ),
            122: ( QtCore.Qt.Key_F11,          '',     None ),
            113: ( QtCore.Qt.Key_F12,          '',     None ),
            144: ( QtCore.Qt.Key_NumLock,      '',     None ),
            145: ( QtCore.Qt.Key_ScrollLock,   '',     None ),
            186: ( QtCore.Qt.Key_Semicolon,    ';',    None ),
            187: ( QtCore.Qt.Key_Equal,        '=',    None ),
            188: ( QtCore.Qt.Key_Comma,        ',',    None ),
            189: ( QtCore.Qt.Key_Minus,        '-',    None ),
            190: ( QtCore.Qt.Key_Period,       '.',    None ),
            191: ( QtCore.Qt.Key_Slash,        '/',    None ),
            192: ( QtCore.Qt.Key_QuoteLeft,    '`',    None ),
            219: ( QtCore.Qt.Key_BracketLeft,  '[',    None ),
            220: ( QtCore.Qt.Key_Backslash,    '\\',   None ),
            221: ( QtCore.Qt.Key_BraceRight,   ']',    None ),
            222: ( QtCore.Qt.Key_QuoteLeft,    "'",    None ),
        
            # Calculate the SHIFT key as 300 + key value
            348: ( QtCore.Qt.Key_ParenRight,   ')',    None ), # Shift+0
            349: ( QtCore.Qt.Key_Exclam,       '!',    None ), # Shift+1
            350: ( QtCore.Qt.Key_At,           '@',    None ), # Shift+2
            351: ( QtCore.Qt.Key_NumberSign,   '#',    None ), # Shift+3
            352: ( QtCore.Qt.Key_Dollar,       '$',    None ), # Shift+4
            353: ( QtCore.Qt.Key_Percent,      '%',    None ), # Shift+5
            354: ( QtCore.Qt.Key_6,            '6',    None ),
            355: ( QtCore.Qt.Key_Ampersand,    '&',    None ), # Shift+7
            356: ( QtCore.Qt.Key_Asterisk,     '*',    None ), # Shift+8
            357: ( QtCore.Qt.Key_ParenLeft,    '(',    None ), # Shift+9
        
            365: ( QtCore.Qt.Key_A,            'A',    None ),
            366: ( QtCore.Qt.Key_B,            'B',    None ),
            367: ( QtCore.Qt.Key_C,            'C',    None ),
            368: ( QtCore.Qt.Key_D,            'D',    None ),
            369: ( QtCore.Qt.Key_E,            'E',    None ),
            370: ( QtCore.Qt.Key_F,            'F',    None ),
            371: ( QtCore.Qt.Key_G,            'G',    None ),
            372: ( QtCore.Qt.Key_H,            'H',    None ),
            373: ( QtCore.Qt.Key_I,            'I',    None ),
            374: ( QtCore.Qt.Key_J,            'J',    None ),
            375: ( QtCore.Qt.Key_K,            'K',    None ),
            376: ( QtCore.Qt.Key_L,            'L',    None ),
            377: ( QtCore.Qt.Key_M,            'M',    None ),
            378: ( QtCore.Qt.Key_N,            'N',    None ),
            379: ( QtCore.Qt.Key_O,            'O',    None ),
            380: ( QtCore.Qt.Key_P,            'P',    None ),
            381: ( QtCore.Qt.Key_Q,            'Q',    None ),
            382: ( QtCore.Qt.Key_R,            'R',    None ),
            383: ( QtCore.Qt.Key_S,            'S',    None ),
            384: ( QtCore.Qt.Key_T,            'T',    None ),
            385: ( QtCore.Qt.Key_U,            'U',    None ),
            386: ( QtCore.Qt.Key_V,            'V',    None ),
            387: ( QtCore.Qt.Key_W,            'W',    None ),
            388: ( QtCore.Qt.Key_X,            'X',    None ),
            389: ( QtCore.Qt.Key_Y,            'Y',    None ),
            390: ( QtCore.Qt.Key_Z,            'Z',    None ),
        
            486: ( QtCore.Qt.Key_Colon,        ':',    None ), # Shift+;
            487: ( QtCore.Qt.Key_Plus,         '+',    None ), # Shift++
            488: ( QtCore.Qt.Key_Less,         '<',    None ), # Shift+,
            489: ( QtCore.Qt.Key_Underscore,   '_',    None ), # Shift+-
            490: ( QtCore.Qt.Key_Greater,      '>',    None ), # Shift+>
            491: ( QtCore.Qt.Key_Question,     '?',    None ), # Shift+?
            492: ( QtCore.Qt.Key_AsciiTilde,   '~',    None ), # Shift+`
            519: ( QtCore.Qt.Key_BraceLeft,    '{',    None ), # Shift+[
            520: ( QtCore.Qt.Key_Bar,          '|',    None ), # Shift+\
            521: ( QtCore.Qt.Key_BraceRight,   '}',    None ), # Shift+]
            522: ( QtCore.Qt.Key_QuoteDbl,     '"',    None ), # Shift+'
        }        
        
    return _SI_TO_QT_KEY_MAP

def _consume_key( ctxt, pressed ):
    """
    build the proper QKeyEvent from Softimage key event and send the it along to the focused widget
    """
    from sgtk.platform.qt import QtCore, QtGui
    
    kcode = ctxt.GetAttribute( 'KeyCode' )
    mask = ctxt.GetAttribute( 'ShiftMask' )

    # Build the modifiers
    modifier = QtCore.Qt.NoModifier
    if ( mask & constants.siShiftMask ):
        if ( kcode + 300 in _get_key_map() ):
            kcode += 300

        modifier |= QtCore.Qt.ShiftModifier

    if ( mask & constants.siCtrlMask ):
        modifier |= QtCore.Qt.ControlModifier

    if ( mask & constants.siAltMask ):
        modifier    |= QtCore.Qt.AltModifier

    # Generate a Qt Key Event to be processed
    result  = _get_key_map().get( kcode )
    if ( result ):

        if ( pressed ):
            event = QtGui.QKeyEvent.KeyPress
        else:
            event = QtGui.QKeyEvent.KeyRelease

        if ( result[2] ):
            modifier |= result[2]

        # Send the event along to the focused widget
        QtGui.QApplication.sendEvent( QtGui.QApplication.instance().focusWidget(), QtGui.QKeyEvent( event, result[0], modifier, result[1] ) )

def _is_qt_widget_focused():
    """
    return true if the global qApp has any focused widgets
    """
    from sgtk.platform.qt import QtGui

    if not QtGui.QApplication.instance():
        return False

    # get the currently focused widget:
    focus_widget = QtGui.QApplication.instance().focusWidget()
    if not focus_widget:
        return False
    
    # Qt widget will retain focus even if the window it's in
    # isn't the foreground window so try to handle this:
    import sys
    if sys.platform == "win32":
        # on Windows, get the forground window and compare
        # to see if it is the Qt window with the focused
        # widget:
        import win32gui
        foreground_hwnd = win32gui.GetForegroundWindow()
        window = focus_widget.window()
        if not window or not foreground_hwnd:
            return False
        
        # need to convert the Qt winId to an HWND
        import ctypes
        ctypes.pythonapi.PyCObject_AsVoidPtr.restype = ctypes.c_void_p
        ctypes.pythonapi.PyCObject_AsVoidPtr.argtypes = [ ctypes.py_object ]
        window_hwnd = ctypes.pythonapi.PyCObject_AsVoidPtr(window.winId())
        
        # and compare
        if window_hwnd != foreground_hwnd:
            return False
    else:
        # check the cursor is inside the widgets top-level window:
        window = focus_widget.window()
        if not window or not window.geometry().contains( QtGui.QCursor.pos() ):
            return False
    
    return True
