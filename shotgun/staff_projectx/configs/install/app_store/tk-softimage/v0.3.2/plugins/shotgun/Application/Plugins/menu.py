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
Implements the Shotgun Menu as a Softimage plug-in
"""

from win32com.client import constants

def XSILoadPlugin( in_reg ):
    """
    Plug-in Load
    """
    in_reg.Author = "Shotgun Software"
    in_reg.Name = "Shotgun Menu"
    in_reg.Major = 1
    in_reg.Minor = 0

    # Make menu dynamic in order to support enable_callback functions
    in_reg.RegisterMenu(constants.siMenuMainTopLevelID, "Shotgun", False, True)

    return True

def XSIUnloadPlugin( in_reg ):
    """
    Plug-in Unload
    """    
    strPluginName = in_reg.Name
    Application.LogMessage(str(strPluginName) + str(" has been unloaded."),constants.siVerbose)
    return True

#########################################################################################################################

def Shotgun_Init( in_ctxt ):
    """
    Initialize the Shotgun menu.  This is called by Softimage every
    time the menu is about to be displayed (because it is dynamic) 
    """
    import sgtk
    sg_menu = ShotgunMenu(in_ctxt.Source)
    
    engine = sgtk.platform.current_engine()
    if engine:
        # ask the engine to build the menu:
        engine.populate_shotgun_menu(sg_menu)
    else:
        # just add a menu showing that Shotgun is disabled:
        def on_shotgun_disabled():
            # (AD) - TODO - show a dialog?
            Application.LogMessage("Shotgun is disabled")
        sg_menu.AddCallbackItem("Shotgun Disabled", on_shotgun_disabled)

class ShotgunMenu(object):
    """
    Wraps the Softimage Menu in a more friendly way
    """
    class CallbackNameGenerator(object):
        """
        Used to generate a unique callback name
        """
        def __init__(self):
            self._id = 0
        def generate_name(self):
            name = "_shotgun_menu_command_%d" % self._id
            self._id += 1
            return name
    
    def __init__(self, si_menu, name_generator=None):
        self._si_menu = si_menu
        self._name_generator = name_generator or ShotgunMenu.CallbackNameGenerator()
        self._sub_menus = []

        # handle different versions of Menu Api
        #if Application.Version().startswith("11.")
        self._si_AddCallbackItem = self._si_menu.AddCallbackItem2 if hasattr(self._si_menu, "AddCallbackItem2") else self._si_menu.AddCallbackItem
        self._si_AddSubMenu = self._si_menu.AddSubMenu2 if hasattr(self._si_menu, "AddSubMenu2") else self._si_menu.AddSubMenu
        
    @property
    def si_menu(self):
        """
        Access the actual Softimage menu object
        """
        return self._si_menu
    
    @property
    def name(self):
        """
        Access the name of the menu
        """
        return self._si_menu.Name
        
    def AddCallbackItem(self, name, callback):
        """
        Wraps the Softimage 'Menu.AddCallBackItem' call in a more callback friendly way.
        """
        # In Maya or Nuke, when you bind a menu item to a callback, you can input the memory address of whatever the callback
        # function is. This makes it a non-issue to generate and update menu items on the fly via the Toolkit configuration. In Softimage,
        # it's not as direct.
        #
        # The Python method Softimage uses for binding a menu callback with the menu item is Menu.AddCallbackItem2(label, callback_name)
        #
        # Rather than passing the memory address of the callback into the second argument, Softimage expects the string name of the
        # handler function. It also assumes that function has already been defined in the memory scope of the Self Installing Plugin that
        # is building the menu item, which is hard to do if the menu and its associated callbacks are being generated on the fly by
        # the toolkit!
        #
        # to overcome this problem, this method wraps the Softimage call and dynamically registers a new callback function in the globals()
        # dictionary which Softimage can find and this in turn will call the intended callback! 
        
        cmd_name = self._name_generator.generate_name()
        #Application.LogMessage("Registering command %s for callback %s" % (cmd_name, callback))
        globals()[cmd_name] = lambda x: callback()
        return self._si_AddCallbackItem(name, cmd_name)
        
    def AddSubMenu(self, name):
        """
        Add the named sub-menu.
        """
        # the menu name should be a unicode object so we cast it to support when, for example, 
        # the context contains info with non-ascii characters
        sub_menu = ShotgunMenu(self._si_AddSubMenu(name.decode("utf-8")), self._name_generator)
        self._sub_menus.append(sub_menu)
        return sub_menu

    def AddSeparatorItem(self):
        """
        Add a seperator to the menu 
        """
        self._si_menu.AddSeparatorItem()

    def close_torn_off_menus(self):
        """
        Helper function that can be used to close all 
        torn-off menus
        """
        all_menus = [self] + self._get_child_menus()
        all_menu_names = [m.name for m in all_menus]
        
        active_layout = Application.Desktop.ActiveLayout
        for view in active_layout.Views:
            if view.Type != "Menu Window":
                continue
            
            view_name = view.GetAttributeValue("metadata")
            if view_name in all_menu_names:
                view.State = 1
        
    def _get_child_menus(self):
        child_menus = []
        for sub_menu in self._sub_menus:
            child_menus.append(sub_menu)
            child_menus.extend(sub_menu._get_child_menus())
        return child_menus        
        
        
        
        
        
        
        
        
        
    