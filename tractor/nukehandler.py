from TrEnvHandler import TrEnvHandler
import logging
import os
import platform

class nukehandler(TrEnvHandler):
    def __init__(self, name, envkeydict, envkeys):
        self.logger = logging.getLogger('tractor-blade')
        self.logger.debug("initializing nukehandler: %s" % (name))
        TrEnvHandler.__init__(self, name, envkeydict, envkeys)

    def updateEnvironment(self, cmd, env, envkeys):
        self.logger.debug("nukehandler.updateEnvironment: %s" % self.name)
        for key in envkeys:
            val = key[4:]
            self.environmentdict['TR_ENV_NUKEVER'] = val

        return TrEnvHandler.updateEnvironment(self, cmd, env, envkeys)

    def remapCmdArgs(self, cmdinfo, launchenv, thisHost):
        self.logger.debug("nukehandler.remapCmdArgs: %s" % self.name)
        argv = TrEnvHandler.remapCmdArgs(self, cmdinfo, launchenv, thisHost)

        nuke_ver = launchenv['TR_ENV_NUKEVER']

        p = platform.system()
        if p == 'Linux' or p == 'Window':
            v = nuke_ver.split('v')
            argv[0] = 'Nuke' + v[0]

        ## Mac OSX
        else:
            argv[0] = 'Nuke' + nuke_ver

        return argv
