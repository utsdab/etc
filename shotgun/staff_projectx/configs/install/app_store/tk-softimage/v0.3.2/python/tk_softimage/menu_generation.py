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
Menu handling for Softimage
"""

import platform
import sys
import os

import sgtk

class MenuGenerator(object):
    """
    Menu generation functionality for Softimage
    """

    def __init__(self, engine):
        self._engine = engine

    ##########################################################################################
    # public methods

    def create_menu(self, menu_handle):
        """
        Render the entire Shotgun menu.
        In order to have commands enable/disable themselves based on the enable_callback,
        re-create the menu items every time.

        By passing the globals() dictionary from the Python Script running in Softimage, we can
        register the callbacks for each Menu handler in the local name space for the Self Installing Plugin
        """
        self._menu_handle = menu_handle

        # add the context item on top of the main menu
        if self._engine.context:
            self._context_menu = self._add_context_menu()

        # enumerate all items and create menu objects for them
        menu_items = []
        for (cmd_name, cmd_details) in self._engine.commands.items():
             menu_items.append( AppCommand(cmd_name, cmd_details))

        # now add favourites
        menu_has_favourites = False
        for fav in self._engine.get_setting("menu_favourites"):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]
            # scan through all menu items
            for cmd in menu_items:
                 if cmd.get_app_instance_name() == app_instance_name and cmd.name == menu_name:
                     if not menu_has_favourites:
                         # add separator:
                         self._menu_handle.AddSeparatorItem() 
                         menu_has_favourites = True
                     
                     # found our match!
                     cmd.add_command_to_menu(self._menu_handle)
                     # mark as a favourite item
                     cmd.favourite = True

        # now go through all of the menu items and
        # separate them out into various sections
        commands_by_app = {}
        context_menu_has_commands = False
        for cmd in menu_items:
            if cmd.get_type() == "context_menu":
                # add this command to the context menu
                if not context_menu_has_commands:
                    # add separator:
                    self._context_menu.AddSeparatorItem()                    
                    context_menu_has_commands = True
                cmd.add_command_to_menu(self._context_menu)
            else:
                # add to list for the main menu:
                app_name = cmd.get_app_name() or "Other Items" # un-parented app 
                if not app_name in commands_by_app:
                    commands_by_app[app_name] = []
                commands_by_app[app_name].append(cmd)

        if commands_by_app:
            # add separator:
            self._menu_handle.AddSeparatorItem()
            # now add all apps to main menu 
            self._add_app_menu(commands_by_app)

    ##########################################################################################
    # context menu and UI

    def _add_context_menu(self):
        """
        Adds a context menu which displays the current context
        """
        ctx = self._engine.context
        ctx_name = str(ctx)

        # create the sub menu object
        ctx_menu = self._menu_handle.AddSubMenu(ctx_name)
        ctx_menu.AddCallbackItem("Jump to Shotgun", lambda: self._jump_to_sg(self._menu_handle))
        ctx_menu.AddCallbackItem("Jump to File System", self._jump_to_fs)

        return ctx_menu

    def _jump_to_sg(self, ctx):
        import webbrowser
        if self._engine.context.entity is None:
            # project-only!
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url,
                                       "Project",
                                       self._engine.context.project["id"])
        else:
            # entity-based
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url,
                                       self._engine.context.entity["type"],
                                       self._engine.context.entity["id"])
        webbrowser.open(url)

    def _jump_to_fs(self):
        """
        Jump from context to FS
        """
        if self._engine.context.entity:
            paths = self._engine.sgtk.paths_from_entity(self._engine.context.entity["type"],
                                                     self._engine.context.entity["id"])
        else:
            paths = self._engine.sgtk.paths_from_entity(self._engine.context.project["type"],
                                                     self._engine.context.project["id"])

        # launch one window for each location on disk
        # todo: can we do this in a more elegant way?
        for disk_location in paths:

            # get the setting
            system = platform.system()

            # run the app
            if system == "Linux":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "Darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "Windows":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)

    ##########################################################################################
    # app menus
    def _add_app_menu(self, commands_by_app):
        """
        Add all apps to the main menu, process them one by one.
        """
        for app_name in sorted(commands_by_app.keys()):
            if len(commands_by_app[app_name]) > 1:
                # more than one menu entry for this app
                # make a sub menu and put all items in the sub menu
                sub_menu = self._menu_handle.AddSubMenu(app_name)
                for cmd in commands_by_app[app_name]:
                    cmd.add_command_to_menu(sub_menu)
            else:
                # this app only has a single entry.
                # display that on the menu
                # todo: Should this be labelled with the name of the app
                # or the name of the menu item? Not sure.
                cmd_obj = commands_by_app[app_name][0]
                if not cmd_obj.favourite:
                    # skip favourites since they are alreay on the menu
                    cmd_obj.add_command_to_menu(self._menu_handle)


class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """
    def __init__(self, name, command_dict):
        self.name = name
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]
        self.favourite = False

    def get_app_name(self):
        """
        Returns the name of the app that this command belongs to
        """
        if "app" in self.properties:
            return self.properties["app"].display_name
        return None

    def get_app_instance_name(self):
        """
        Returns the name of the app instance, as defined in the environment.
        Returns None if not found.
        """
        if "app" not in self.properties:
            return None

        app_instance = self.properties["app"]
        engine = app_instance.engine

        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                # found our app!
                return app_instance_name

        return None

    def get_type(self):
        """
        returns the command type. Returns node, custom_pane or default
        """
        return self.properties.get("type", "default")

    def add_command_to_menu(self, menu):
        """
        Adds an app command to the menu
        """
        enabled = True

        if "enable_callback" in self.properties:
            enabled = self.properties["enable_callback"]()

        # If the callback triggers an engine restart / menu teardown while the menu is still open
        # (or a Toolkit app returns from its execution and the menu has been deleted), Softimage will crash.
        # Possible workaround is to use QTimer.singleShot, which requires PySide and a running Qt event loop.
        # Using singleShot defers execution until events are processed again.  A modal dialog will block events
        # and if the modal causes a menu teardown the crash ensues.
        from sgtk.platform.qt import QtCore
        menu_item = menu.AddCallbackItem(self.name, lambda: QtCore.QTimer.singleShot(100, self.callback))
        menu_item.Enabled = enabled
