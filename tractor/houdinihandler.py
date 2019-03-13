from TrEnvHandler import TrEnvHandler
import logging
import os
import platform

# houdini_setup - aka $HFS
# /Applications/Houdini/Houdini17.0.416/Frameworks/Houdini.framework/Versions/Current/Resources
# /opt/sidefx/hfs17.0.416

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
            #  "TR_ENV_HOUDINIVER": "17.0.416",
            head = key[:7]
            val = key[7:]
            bits = val.split(".")
            maj = bits[0]
            min = bits[1]
            build = bits[2]

            if head == 'houdini':
                self.environmentdict['TR_ENV_HOUDINIVER'] = val
                self.environmentdict['TR_ENV_HOUDINI_MAJOR_RELEASE'] = maj
                self.environmentdict['TR_ENV_HOUDINI_MINOR_RELEASE'] = min
                self.environmentdict['TR_ENV_HOUDINI_BUILD'] = build

            p = platform.system()
            if p == 'Linux':
                self.environmentdict['TR_ENV_HFS'] = "/opt/sidefx/hfs{}.{}.{}".format(maj,min,build)
            elif p  == 'Window':
                self.environmentdict['TR_ENV_HFS'] = "/Programs/sidefx/hfs{}.{}.{}".format(maj,min,build)
            ## Mac OSX
            else:
                self.environmentdict['TR_ENV_HFS'] = "/Applications/Houdini/Houdini{}.{}.{}/Frameworks/Houdini.framework/Versions/Current/Resources".format(maj,min,build)
                self.environmentdict['TR_ENV_CURRENT_HFS'] = "/Applications/Houdini/Current/Frameworks/Houdini.framework/Versions/Current/Resources".format(maj,min,build)


        return TrEnvHandler.updateEnvironment(self, cmd, env, envkeys)

    # def remapCmdArgs(self, cmdinfo, launchenv, thisHost):
    #     self.logger.debug("houdinihandler.remapCmdArgs: %s" % self.name)
    #
    #     if launchenv['TR_ENV_HOUDINIVER']:
    #         argv = TrEnvHandler.remapCmdArgs(self, cmdinfo, launchenv, thisHost)
    #         houdini_ver = launchenv['TR_ENV_HOUDINIVER']
    #         p = platform.system()
    #
    #         if p == 'Linux':
    #             argv[0] = 'houdini' + houdini_ver
    #
    #         elif p == 'Window':
    #             argv[0] = 'houdini' + houdini_ver
    #
    #         ## Mac OSX
    #         else:
    #             argv[0] = 'houdini' + houdini_ver
    #
    #     return argv
