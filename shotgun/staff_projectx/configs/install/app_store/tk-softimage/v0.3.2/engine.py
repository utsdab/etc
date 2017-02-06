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
Implements the Softimage Engine for the Shotgun Pipeline Toolkit.
"""

import sys
import os

import sgtk
from sgtk.platform import Engine

import win32com
from win32com.client import Dispatch, constants
Application = Dispatch("XSI.Application").Application
XSIUIToolkit = Dispatch("XSI.UIToolkit")

class SoftimageEngine(Engine):

    ##########################################################################################
    # init and destroy

    def init_engine(self):
        """
        Called when the engine is being initialized
        """
        
        # determine if this is a tested version:
        is_certified_version = False
        version_str = Application.version()
        version_parts = version_str.split(".")
        if version_parts and version_parts[0].isnumeric():
            version_major = int(version_parts[0])
            if sys.platform == "win32":
                if (version_major >= 10     # >= Softimage 2012
                    and version_major <= 11 # <= Softimage 2013
                    ): 
                    is_certified_version = True
            elif sys.platform == "linux2": 
                # This is still marginally experimental
                if version_major == 11:     # == Softimage 2013
                    is_certified_version = True
                
        if not is_certified_version:
            # show a warning:
            msg = ("The Shotgun Pipeline Toolkit has not yet been fully tested with Softimage %s. "
                   "You can continue to use the Toolkit but you may experience bugs or "
                   "instability.\n\n"
                   "Please report any issues you see to support@shotgunsoftware.com" 
                   % (version_str))
            
            if self.has_ui and "SGTK_SOFTIMAGE_VERSION_WARNING_SHOWN" not in os.environ:
                # have to call RedrawUI() otherwise Softimage will crash!
                Application.Desktop.RedrawUI()
                XSIUIToolkit.MsgBox("Warning - Shotgun Pipeline Toolkit!\n\n%s" % msg)
                os.environ["SGTK_SOFTIMAGE_VERSION_WARNING_SHOWN"] = "1"
                
            self.log_warning(msg)

        try:
            self.log_user_attribute_metric("Softimage version", version_str)
        except:
            # ignore all errors. ex: using a core that doesn't support metrics
            pass
            
        # Set the Softimage project based on config
        self._set_project()
        
        # menu:
        self._menu = None
        tk_softimage = self.import_module("tk_softimage")
        self._menu_generator = tk_softimage.MenuGenerator(self)
        self._shotgun_plugin_path = os.path.join(self.disk_location, "plugins", "shotgun", "Application", "Plugins")
        
        
    def destroy_engine(self):
        """
        Called when engine is destroyed
        """
        self.log_debug("%s: Destroying..." % self)

        # clean up UI:
        if self.has_ui:
            if self._menu:
                # close any torn-off menus:
                self._menu.close_torn_off_menus()
        
            # Unload the menu plugin
            Application.UnloadPlugin(os.path.join(self._shotgun_plugin_path, "menu.py"))

            # unload the qtevents plugin
            Application.UnloadPlugin(os.path.join(self._shotgun_plugin_path, "qt_events.py"))

    @property
    def has_ui(self):
        """
        Detect and return if Softimage is running in batch mode
        """
        return Application.Interactive

    def pre_app_init(self):
        """
        Runs after the engine is set up but before any apps have been initialized.
        """        
        # unicode characters returned by the shotgun api need to be converted
        # to display correctly in all of the app windows
        from tank.platform.qt import QtCore
        # tell QT to interpret C strings as utf-8
        utf8 = QtCore.QTextCodec.codecForName("utf-8")
        QtCore.QTextCodec.setCodecForCStrings(utf8)
        self.log_debug("set utf-8 codec for widget text")

    def post_app_init(self):
        """
        Called when all apps have initialized
        """
        if self.has_ui:

            # ensure we have a QApplication            
            self._initialise_qapplication()
                        
            # Re-load plug-ins
            Application.UnloadPlugin(os.path.join(self._shotgun_plugin_path, "menu.py"))
            Application.UnloadPlugin(os.path.join(self._shotgun_plugin_path, "qt_events.py"))
            
            Application.LoadPlugin(os.path.join(self._shotgun_plugin_path, "menu.py"))
            Application.LoadPlugin(os.path.join(self._shotgun_plugin_path, "qt_events.py"))

    def populate_shotgun_menu(self, menu):
        """
        Use the menu generator to populate the Shotgun menu
        """
        self._menu = menu
        self._menu_generator.create_menu(self._menu)

    ##########################################################################################
    # logging

    def log_debug(self, msg):
        if self.get_setting("debug_logging", False):
            Application.LogMessage("Shotgun: %s" % msg, constants.siInfo)

    def log_info(self, msg):
        Application.LogMessage("Shotgun: %s" % msg, constants.siInfo)

    def log_warning(self, msg):
        Application.LogMessage("Shotgun: %s" % msg, constants.siWarning)

    def log_error(self, msg):
        import traceback
        tb = traceback.print_exc()
        if tb:
            msg = tb+"\n"+msg
        Application.LogMessage("Shotgun: %s" % msg, constants.siError)

    ##########################################################################################
    # scene and project management

    def _set_project(self):
        """
        Set the softimage project
        """
        setting = self.get_setting("template_project")
        if setting is None:
            return

        tmpl = self.sgtk.templates.get(setting)
        fields = self.context.as_template_fields(tmpl)
        proj_path = tmpl.apply_fields(fields)
        self.log_info("Setting Softimage project to '%s'" % proj_path)

        try:
            # test to see if the project has already been set to this path
            # Application.ActiveProject.Path returns a unicode object. If the path contains
            # non-ascii characters, the comparison will fail since the str and unicode objects
            # cannot be compared, so we convert the unicode object to a utf-8 string.
            if (Application.ActiveProject.Path 
                and os.path.normpath(Application.ActiveProject.Path).lower().encode("utf-8") == os.path.normpath(proj_path).lower()):
                # project is already set to this path so no need to do anything!
                return
            
            # make sure the project exists:
            created_proj = Application.CreateProject(proj_path)
            if not created_proj:
                raise

            # and set it:
            Application.ActiveProject = proj_path
        except:
            self.log_error("Error setting Softimage Project: %s" % proj_path)

    ##########################################################################################
    # pyside / qt

    def _define_qt_base(self):
        """
        Because Softimage does not include PySide/Qt distributions but does use it's own
        special version of Python, we have to distribute full versions for the engine to
        function.
        
        However, because these are quite large, they have now been split out into a separate
        framework (tk-framework-softimageqt).
        
        This function now calls out to that framework (via the tk_softimage module) to
        define the qt base.
        """
        tk_softimage = self.import_module("tk_softimage")
        return tk_softimage.define_qt_base()

    def _get_dialog_parent(self):
        """
        Get the QWidget parent for all dialogs created through
        show_dialog & show_modal.
        """
        if not hasattr(self, "_qt_parent_widget"):
            tk_softimage = self.import_module("tk_softimage")
            self._qt_parent_widget = tk_softimage.get_qt_parent_window()
        return self._qt_parent_widget
    
    def show_modal(self, title, bundle, widget_class, *args, **kwargs):
        """
        Shows a modal dialog window in a way suitable for this engine. The engine will attempt to
        integrate it as seamlessly as possible into the host application. This call is blocking
        until the user closes the dialog.

        :param title: The title of the window
        :param bundle: The app, engine or framework object that is associated with this window
        :param widget_class: The class of the UI to be constructed. This must derive from QWidget.

        Additional parameters specified will be passed through to the widget_class constructor.

        :returns: (a standard QT dialog status return code, the created widget_class instance)
        """
        if not self.has_ui:
            self.log_error("Sorry, this environment does not support UI display! Cannot show "
                           "the requested window '%s'." % title)
            return    
        
        from PySide import QtGui

        # create the dialog:
        dialog, widget = self._create_dialog_with_widget(title, bundle, widget_class, *args, **kwargs)
        
        # show the dialog in application modal if possible:
        status = QtGui.QDialog.Rejected
        status = self._run_application_modal(dialog.exec_)

        return status, widget
    
    def _initialise_qapplication(self):
        """
        Ensure the QApplication is initialized
        """
        from sgtk.platform.qt import QtGui
        if not QtGui.QApplication.instance():
            
            self.log_debug("Initialising main QApplication...")
            qt_app = QtGui.QApplication([])
            qt_app.setWindowIcon(QtGui.QIcon(self.icon_256))
            qt_app.setQuitOnLastWindowClosed(False)
            
            # set up the dark style
            self._initialize_dark_look_and_feel()
        
    
    def _override_qmessagebox_methods(self, QtGui):
        """
        Handle common QMessageBox methods to better handle
        parenting and modality 
        """
        
        information_fn = QtGui.QMessageBox.information
        critical_fn = QtGui.QMessageBox.critical
        question_fn = QtGui.QMessageBox.question
        warning_fn = QtGui.QMessageBox.warning
        
        def _fix_parent_in_args(*args, **kwargs):
            if args:
                # parent is first arg:
                if args[0] == None:
                    qt_parent_widget = self._get_dialog_parent()
                    args = (qt_parent_widget, ) + args[1:]
            else:
                if "parent" in kwargs:
                    if kwargs["parent"] == None:
                        qt_parent_widget = self._get_dialog_parent()
                        kwargs["parent"] = qt_parent_widget
                else:
                    # parent not set at all!
                    args = (qt_parent_widget, )
                
            return args, kwargs
        
        @staticmethod
        def _info_wrapper(*args, **kwargs):
            args, kwargs = _fix_parent_in_args(*args, **kwargs)
            func = lambda a=args, k=kwargs: information_fn(*a, **k)
            return self._run_application_modal(func)
        
        @staticmethod
        def _critical_wrapper(*args, **kwargs):
            args, kwargs = _fix_parent_in_args(*args, **kwargs)
            func = lambda a=args, k=kwargs: critical_fn(*a, **k)
            return self._run_application_modal(func)
        
        @staticmethod
        def _question_wrapper(*args, **kwargs):
            args, kwargs = _fix_parent_in_args(*args, **kwargs)
            func = lambda a=args, k=kwargs: question_fn(*a, **k)
            return self._run_application_modal(func)
        
        @staticmethod
        def _warning_wrapper(*args, **kwargs):
            args, kwargs = _fix_parent_in_args(*args, **kwargs)
            func = lambda a=args, k=kwargs: warning_fn(*a, **k)
            return self._run_application_modal(func)

        QtGui.QMessageBox.information = _info_wrapper
        QtGui.QMessageBox.critical = _critical_wrapper
        QtGui.QMessageBox.question = _question_wrapper
        QtGui.QMessageBox.warning = _warning_wrapper
    
    
    def _run_application_modal(self, func):
        """
        Run the specified function application modal if
        possible.
        """
        ret = None
        if sys.platform == "win32":
            
            # when we show a modal dialog, the application should be disabled.
            # However, because the QApplication doesn't have control over the
            # main Softimage window we have to do this ourselves...
            import win32api, win32gui
            tk_softimage = self.import_module("tk_softimage")

            foreground_window = None
            saved_state = []
            try:
                # find all windows and save enabled state:
                foreground_window = win32gui.GetForegroundWindow()
                #self.log_debug("Disabling main application windows before showing modal dialog")
                found_hwnds = tk_softimage.find_windows(thread_id = win32api.GetCurrentThreadId(), stop_if_found=False)
                for hwnd in found_hwnds:
                    enabled = win32gui.IsWindowEnabled(hwnd)
                    saved_state.append((hwnd, enabled))
                    if enabled:
                        # disable the window:
                        win32gui.EnableWindow(hwnd, False)

                # run function
                ret = func()
                
            except Exception, e:
                self.log_error("Error showing modal dialog: %s" % e)
            finally:
                #self.log_debug("Restoring state of main application windows")
                # kinda important to ensure we restore other window state:
                for hwnd, state in saved_state:
                    if win32gui.IsWindowEnabled(hwnd) != state:
                        # restore the state:
                        win32gui.EnableWindow(hwnd, state)
                if foreground_window:
                    win32gui.SetForegroundWindow(foreground_window)
        else:
            # show dialog:
            ret = func()
            
        return ret        
        
        
        
        
        
    
    
