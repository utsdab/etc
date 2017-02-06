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
Framework containing PySide distributions for the Softimage engine
"""

import sgtk
import sys
import os

class SoftimageQtFramework(sgtk.platform.Framework):

    ##########################################################################################
    # init and destroy
            
    def init_framework(self):
        self.log_debug("%s: Initializing..." % self)
    
    def destroy_framework(self):
        self.log_debug("%s: Destroying..." % self)
        
    def define_qt_base(self):
        """
        Load PySide/PyQt to use for the tk-softimage engine.  Returns a dictionary of the modules required
        by the engine to support Qt UI's
        """
        # proxy class used when QT does not exist on the system.
        # this will raise an exception when any QT code tries to use it
        class QTProxy(object):                        
            def __getattr__(self, name):
                raise sgtk.TankError("Looks like you are trying to run an App that uses a QT "
                                     "based UI, however the Softimage engine could not find a PyQt "
                                     "or PySide installation in your python system path. We " 
                                     "recommend that you install PySide if you want to "
                                     "run UI applications from within Softimage.")
        
        base = {"qt_core": QTProxy(), "qt_gui": QTProxy(), "dialog_base": None}
        
        have_qt = False
        if not have_qt:
            try:
                from PySide import QtCore, QtGui
                import PySide
                
                base["qt_core"] = QtCore
                base["qt_gui"] = QtGui
                base["dialog_base"] = QtGui.QDialog
                self.log_debug("Successfully initialized PySide %s located in %s." % (PySide.__version__, PySide.__file__))
                have_qt = True
            except ImportError:
                pass
            except Exception, e:
                self.log_warning("Error setting up pyside. Pyside based UI support will not "
                                 "be available: %s" % e)
        
        if not have_qt:
            try:
                from PyQt4 import QtCore, QtGui
                import PyQt4
               
                # hot patch the library to make it work with pyside code
                QtCore.Signal = QtCore.pyqtSignal
                QtCore.Slot = QtCore.pyqtSlot
                QtCore.Property = QtCore.pyqtProperty             
                base["qt_core"] = QtCore
                base["qt_gui"] = QtGui
                base["dialog_base"] = QtGui.QDialog
                self.log_debug("Successfully initialized PyQt %s located in %s." 
                               % (QtCore.PYQT_VERSION_STR, PyQt4.__file__))
                have_qt = True
            except ImportError:
                pass
            except Exception, e:
                self.log_warning("Error setting up PyQt. PyQt based UI support will not "
                                 "be available: %s" % e)
                
        if not have_qt:
            # lets try the version of PySide included with the framework:
            pyside_root = None            
            if sys.platform == "win32":
                if sys.version_info[0] == 2 and sys.version_info[1] == 6:
                    pyside_root = os.path.join(self.disk_location, "resources", "pyside120_py26_qt484_win64")
                elif sys.version_info[0] == 2 and sys.version_info[1] == 7:
                    pyside_root = os.path.join(self.disk_location, "resources", "pyside112_py27_qt484_win64")
                    
            elif sys.platform == "linux2":
                pyside_root = os.path.join(self.disk_location, "resources", "pyside121_py25_qt485_linux", "python")
            else:
                pass

            if pyside_root:
                self.log_debug("Attempting to import PySide from %s" % pyside_root)
                if pyside_root not in sys.path:
                    sys.path.append(pyside_root)

                try:
                    from PySide import QtCore, QtGui
                    import PySide
                    
                    base["qt_core"] = QtCore
                    base["qt_gui"] = QtGui
                    base["dialog_base"] = QtGui.QDialog
                    self.log_debug("Successfully initialized PySide %s located in %s." 
                                   % (PySide.__version__, PySide.__file__))
                    self._has_ui = True
                except ImportError:
                    pass
                except Exception, e:
                    self.log_warning("Error setting up PySide. Pyside based UI support will not "
                                     "be available: %s" % e)        
        
        return base



