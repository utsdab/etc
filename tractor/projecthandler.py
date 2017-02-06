from TrEnvHandler import TrEnvHandler
import logging
import platform
class projecthandler(TrEnvHandler):
    def __init__(self, name, envkeydict, envkeys):
        self.logger = logging.getLogger("tractor-blade")
        self.logger.info("initializing projecthandler: %s" % (name))
        TrEnvHandler.__init__(self, name, envkeydict, envkeys)

    def initLocalVars(self):
        '''  type is project or work or deva
             show is the student name or the project name depending on type
             proj is the maya project name
             scene is the maya scene file
             task is not yet implemented and more suitable to a larger production crew.
             /Volumes/dabrender/$TYPE/$SHOW/$SCENE/scene/$SHOT
        '''
        self.type = None
        self.show = None
        self.proj = None
        self.scene = None
        self.scenename = None
        #self.task = None

    def updateEnvironment(self, cmd, env, envkeys):
        self.logger.debug("projecthandler.updateEnvironment: %s" % repr(envkeys))
        # Local vars should be initialized in call to updateEnvironment()
        self.initLocalVars()
        
        if envkeys and type(envkeys) == type([]):
            for envkey in envkeys:
                try:
                    key,val = envkey.split("=")
                    if key == "TYPE":
                        self.type = val
                        env["TYPE"] = self.type
                    if key == "SHOW":
                        self.show = val
                        env["SHOW"] = self.show
                    if key == "SCENE":
                        self.scene = val
                        env["SCENE"] = self.scene
                    if key == "SCENENAME":
                        self.scenename = val
                        env["SCENENAME"] = self.scenename
                    if key == "PROJECT":
                        self.project = val
                        env["PROJECT"] = self.project
                    #elif key == "TASK":
                        #self.task = val
                        #env["TASK"] = self.task
                except:
                    self.logger.warn("failed to split envkey {}".format(envkey))

        return TrEnvHandler.updateEnvironment(self, cmd, env, envkeys)

    def remapCmdArgs(self, cmdinfo, launchenv, thisHost):
        self.logger.debug("projecthandler.remapCmdArgs: %s" % self.name)
        argv = TrEnvHandler.remapCmdArgs(self, cmdinfo, launchenv, thisHost)
        self.logger.info("type: %s, show: %s, proj: %s, scene: %s, scenename: %s" %
            (self.type, self.show, self.project, self.scene, self.scenename ))

        # indicate command was launched by tractor
        launchenv["TRACTOR"] = "1"

        if argv[0] == "render" and "RMANTREE" in launchenv:
            argv[0] = os.path.join(launchenv["RMANTREE"],"bin","prman")
            argv[1:1] = ["-statsfile", "%s-%s-%s-%s" % (self.type,self.show, self.project, self.scene)]

        # on windows for add the Visual Studio default libs and includes
        p = platform.platform()
        if p.find("Windows") != -1:
            if launchenv.has_key("INCLUDE"):
                launchenv["INCLUDE"] += ";" + launchenv["VCINCLUDE"]
            else:
                launchenv["INCLUDE"] = launchenv["VCINCLUDE"]

            if launchenv.has_key("LIB"):
                launchenv["LIB"] += ";" + launchenv["VCLIB"]
            else:
                launchenv["LIB"] = launchenv["VCLIB"]

        return argv

    def debug(self):
        self.logger.debug("projecthandler.debug: %s" % self.name)
        TrEnvHandler.debug(self)


