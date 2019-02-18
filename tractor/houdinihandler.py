from TrEnvHandler import TrEnvHandler
import logging
import os
import platform


# /Applications/Houdini/Houdini17.0.416/Frameworks/Houdini.framework/Versions/Current/Resources
class houdinihandler(TrEnvHandler):
    def __init__(self, name, envkeydict, envkeys):
        self.logger = logging.getLogger('tractor-blade')
        self.logger.debug("initializing houdinihandler: %s" % (name))
        TrEnvHandler.__init__(self, name, envkeydict, envkeys)

    def updateEnvironment(self, cmd, env, envkeys):
        self.logger.debug("houdinihandler.updateEnvironment: %s" % self.name)
        for key in envkeys:
            # Houdini
            # 1234567
            val = key[7:]
            self.environmentdict['TR_ENV_HOUDINIVER'] = val

        return TrEnvHandler.updateEnvironment(self, cmd, env, envkeys)

    def remapCmdArgs(self, cmdinfo, launchenv, thisHost):
        self.logger.debug("houdinihandler.remapCmdArgs: %s" % self.name)
        argv = TrEnvHandler.remapCmdArgs(self, cmdinfo, launchenv, thisHost)

        houdini_ver = launchenv['TR_ENV_HOUDINIVER']

        p = platform.system()
        if p == 'Linux' or p == 'Window':
            v = houdini_ver.split('v')
            argv[0] = 'Houdini' + v[0]

        ## Mac OSX
        else:
            argv[0] = 'Houdini' + houdini_ver

        return argv
