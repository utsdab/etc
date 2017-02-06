from TrEnvHandler import TrEnvHandler
import logging
import os
import platform

class mayahandler(TrEnvHandler):
    def __init__(self, name, envkeydict, envkeys):
        self.logger = logging.getLogger('tractor-blade')
        self.logger.debug("initializing mayahandler: %s" % (name))
        TrEnvHandler.__init__(self, name, envkeydict, envkeys)

    def updateEnvironment(self, cmd, env, envkeys):
        self.logger.debug("mayahandler.updateEnvironment: %s" % self.name)
        for key in envkeys:
            val = key[4:]
            self.environmentdict['TR_ENV_MAYAVER'] = val
            ml = TrEnvHandler.locateMayaDirectory(self, val)
            if ml:
                self.environmentdict['TR_ENV_MAYALOCATION'] = ml

        # The mayahandler environment expects these vars to be set
        # preset to "" if they don't exist in the blade environment
        plat = platform.system()
        if plat == 'Darwin':
            if not env.has_key("DYLD_LIBRARY_PATH"):
                env['DYLD_LIBRARY_PATH'] = "" 
        elif plat == 'Linux':
            if not env.has_key("LD_LIBRARY_PATH"):
                env['LD_LIBRARY_PATH'] = "" 
            
        if not env.has_key("MAYA_MODULE_PATH"):
            env['MAYA_MODULE_PATH'] = "" 

        return TrEnvHandler.updateEnvironment(self, cmd, env, envkeys)

