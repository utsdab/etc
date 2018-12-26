from TrEnvHandler import TrEnvHandler
import logging
import os
import platform

class houdinihandler(TrEnvHandler):
    def __init__(self, name, envkeydict, envkeys):
        self.logger = logging.getLogger('tractor-blade')
        self.logger.debug("initializing nukehandler: %s" % (name))
        TrEnvHandler.__init__(self, name, envkeydict, envkeys)

    def updateEnvironment(self, cmd, env, envkeys):
        self.logger.debug("houdinihandler.updateEnvironment: %s" % self.name)
        for key in envkeys:
            val = key[4:]
            self.environmentdict['TR_ENV_HOUDINIVER'] = val

        return TrEnvHandler.updateEnvironment(self, cmd, env, envkeys)

    def remapCmdArgs(self, cmdinfo, launchenv, thisHost):
        self.logger.debug("houdinihandler.remapCmdArgs: %s" % self.name)
        argv = TrEnvHandler.remapCmdArgs(self, cmdinfo, launchenv, thisHost)

        nuke_ver = launchenv['TR_ENV_HOUDINIVER']

        p = platform.system()
        if p == 'Linux' or p == 'Window':
            v = nuke_ver.split('v')
            argv[0] = 'Houdini' + v[0]

        ## Mac OSX
        else:
            argv[0] = 'Houdini' + nuke_ver

        return argv
