from TrEnvHandler import TrEnvHandler
import logging
import os
import platform

class proxyhandler(TrEnvHandler):
    def __init__(self, name, envkeydict, envkeys):
        self.logger = logging.getLogger('tractor-blade')
        self.logger.debug("initializing proxyhandler: %s" % (name))
        TrEnvHandler.__init__(self, name, envkeydict, envkeys)

    def updateEnvironment(self, cmd, env, envkeys):
        self.logger.debug("proxyhandler.updateEnvironment: %s" % self.name)
        for key in envkeys:
            val = key[4:]
            self.environmentdict['TR_ENV_RVIO'] = val

        return TrEnvHandler.updateEnvironment(self, cmd, env, envkeys)

    def remapCmdArgs(self, cmdinfo, launchenv, thisHost):
        #self.logger.debug("nukehandler.remapCmdArgs: %s" % self.name)
        argv = TrEnvHandler.remapCmdArgs(self, cmdinfo, launchenv, thisHost)

        #nuke_ver = launchenv['TR_ENV_NUKEVER']
        #rvio_ver = launchenv['TR_ENV_RVIO']

        #p = platform.system()
        #if p == 'Linux' or p == 'Window':
        #    v = nuke_ver.split('v')
        #    argv[0] = 'Nuke' + v[0]

        ## Mac OSX
        #else:
        #    argv[0] = 'Nuke' + nuke_ver

        return argv
