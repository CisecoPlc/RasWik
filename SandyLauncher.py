#!/usr/bin/env python
import Tkinter as tk
import sys, os
import argparse
import urllib2
import ConfigParser

class SandyLauncher:
    def __init__(self):
        self.debug = True # untill we read config or get command line
        self.configFileDefault = "Python/sandy_default.cfg"
        self.configFile = "Python/sandy.cfg"
        self._running = False
    
    def on_excute(self):
        self.readConfig()
        self.checkArgs()

        self._running = True

        try:
            self.runLauncher()
        except KeyboardInterrupt:
            self.debugPrint("Keyboard Quit")
            self._running = False
        
        self.cleanUp()
    
    def cleanUp(self):
        self.debugPrint("Clean up and exit")
        # disconnect resources
        # kill childs??
        self.writeConfig()
    
    def debugPrint(self, msg):
        if self.debug:
            print(msg)

    def checkArgs(self):
        self.debugPrint("Parse Args")
        parser = argparse.ArgumentParser(description='Sandy Launcher')
        parser.add_argument('-u', '--noupdate', help='disable checking for update', action='store_false')
        parser.add_argument('-d', '--debug', help='Extra Debug Output, overides sandy.cfg setting', action='store_true')
        
        args = parser.parse_args()
        
        if args.debug:
            self.debug = True

        if args.noupdate:
            self.checkForUpdate()

    def checkForUpdate(self):
        self.debugPrint("Checking for update")
        # go download version file
        try:
            request = urllib2.urlopen(self.config.get('Update', 'updateurl') +
                                      self.config.get('Update', 'versionfile'))
            self.newVersion = request.read()

        except urllib2.HTTPError, e:
            self.debugPrint('Unable to get latest version info - HTTPError = ' +
                            str(e.reason))
            sys.exit(2)

        except urllib2.URLError, e:
            self.debugPrint('Unable to get latest version info - URLError = ' +
                            str(e.reason))
            sys.exit(2)

        except httplib.HTTPException, e:
            self.debugPrint('Unable to get latest version info - HTTPException')
            sys.exit(2)

        except Exception, e:
            import traceback
            self.debugPrint('Unable to get latest version info - Exception = ' +
                            traceback.format_exc())
            sys.exit(2)

        try:
            f = open('Python/' + self.config.get('Update', 'versionfile'))
            self.currentVersion = f.read()
            f.close()
        except:
            pass

        self.debugPrint("Latest Version: {}, Current Version: {}".format(self.newVersion, self.currentVersion))
    
    def downloadUpdate(self):
        self.debugPrint("Downloading Update Zip")
    
    def manualZipUpdate(self):
        self.debugPrint("Location Zip for Update")
            
    def doUpdate(self, path):
        self.debugPrint("Doing update")

    def runLauncher(self):
        self.debugPrint("Running Main Launcher")

    def readConfig(self):
        self.debugPrint("Reading Config")

        self.config = ConfigParser.SafeConfigParser()
        
        # load defaults
        self.config.readfp(open(self.configFileDefault))
    
        # read the user config file
        self.config.read(self.configFile)
        
        self.debug = self.config.getboolean('Shared', 'debug')
    
    def writeConfig(self):
        self.debugPrint("Writing Config")
        with open(self.configFile, 'wb') as configfile:
            self.config.write(configfile)

if __name__ == "__main__":
    app = SandyLauncher()
    app.on_excute()

