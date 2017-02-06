# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.



"""
Before App Launch Hook

This hook is executed prior to application launch and is useful if you need
to set environment variables or run scripts as part of the app initialization.
"""

import os
import sys
import tank
import pprint
import subprocess
import pickle


class BeforeMayaLaunch(tank.Hook):
    """
    Hook to set up the system prior to app launch.
    """
    
    def execute(self, app_path, app_args, version, **kwargs):
        """
        The execute functon of the hook will be called prior to starting the required application        
        
        :param app_path: (str) The path of the application executable
        :param app_args: (str) Any arguments the application may require
        :param version: (str) version of the application being run if set in the "versions" settings
                              of the Launcher instance, otherwise None

        """

        # accessing the current context (current shot, etc)
        # can be done via the parent object
        #
        # > multi_launchapp = self.parent
        # > current_entity = multi_launchapp.context.entity
        
        # you can set environment variables like this:
        MAYA_VERSION="2017"
        RMAN_VERSION="21.2"
        TRACTOR_VERSION="2.2"

        _envars={
                    "DABRENDER"  : "/Volumes/dabrender",\
                    "DABWORK"    : "/Volumes/dabrender/work",\
                    "DABUSR"     : "/Volumes/dabrender/usr",\
                    "DABUSR"     : "/Volumes/dabrender/usr",\
                    "DABASSETS"  : "/Volumes/dabrender/assets",\
                    "CONFIG"     : "/Volumes/dabrender/userprefs/{}/".format("120988"),\
                    "RMAN_VERSION"    : RMAN_VERSION,\
                    "MAYA_VERSION"    : MAYA_VERSION,\
                    "TRACTOR_VERSION" : TRACTOR_VERSION,\
                    "RMANTREE"      : "/Applications/Pixar/RenderManProServer-{}".format(RMAN_VERSION),\
                    "RMSTREE"       : "/Applications/Pixar/RenderManStudio-{}-maya{}".format(RMAN_VERSION,MAYA_VERSION),\
                    "RMS_SCRIPT_PATHS"     : "/Volumes/dabrender/usr",\
                    "RDIR"          : "/Volumes/dabrender/usr",\
                    "MAYA_APP_DIR"  : "/Volumes/dabrender/work/user_work/matthewgidney/mayaConfig"
                }

        for key in _envars.keys():
            os.environ[key] = _envars[key]
            tank.util.append_path_to_env_var(key, _envars[key])

        
        # if you are using a shared hook to cover multiple applications,
        # you can use the engine setting to figure out which application 
        # is currently being launched:
        #
        
        # multi_launchapp = self.parent
        # current_entity = multi_launchapp.context.entity
        # 
        # home_path = os.path.expanduser("~")
        # profile_path = "%s/.profile" % home_path
        # cmd = 'source %s' % profile_path
        # dump = '/usr/bin/python -c "import os,pickle; print pickle.dumps(os.environ)"'
        # 
        # try:
        #     penv = os.popen('%s && %s' % (cmd,dump))
        # except OSError as e:
        #     multi_launchapp.log_info("Could not create environment context!")
        #     multi_launchapp.log_info("OSError %s" % e.errno)  
        #     multi_launchapp.log_info("OSError %s" % e.filename)
        # except:
        #     multi_launchapp.log_info("Could not create environment context!" + sys.exc_info()[0])
        #     
        # env = pickle.loads(penv.read())
        # os.environ = env
        # 
        # # do not pass the DISPLAY! 
        # env_exclude = ["DISPLAY"]
        # 
        # for key, var in os.environ.iteritems():
        #     if not key in env_exclude:
        #         tank.util.append_path_to_env_var(key, var)
