import os
import sys
import time
import types

if not os.path.exists('logs/'):
    os.mkdir('logs/')
    print('Made new directory for logs')

ltime = 1 and time.localtime()
logSuffix = '%02d%02d%02d_%02d%02d%02d' % (ltime[0] - 2000,  ltime[1], ltime[2],
                                           ltime[3], ltime[4], ltime[5])
logfile = os.path.join('logs', 'toontown-' + logSuffix + '.log')

class LogAndOutput:
    def __init__(self, orig, log):
        self.orig = orig
        self.log = log

    def write(self, str):
        self.log.write(str)
        self.log.flush()
        self.orig.write(str)
        self.orig.flush()

    def flush(self):
        self.log.flush()
        self.orig.flush()

log = open(logfile, 'a')
logOut = LogAndOutput(sys.__stdout__, log)
logErr = LogAndOutput(sys.__stderr__, log)
sys.stdout = logOut
sys.stderr = logErr

print('\n\nStarting Toontown...')

if 1:
    print('Current time: ' + time.asctime(time.localtime(time.time())) + ' ' + time.tzname[0])
    print('sys.path = ', sys.path)
    print('sys.argv = ', sys.argv)

from otp.launcher.LauncherBase import LauncherBase
from otp.otpbase import OTPLauncherGlobals
from toontown.toonbase import TTLocalizer

from panda3d.core import *

class ToontownLauncher(LauncherBase):
    def __init__(self):
        pass

    def getValue(self, key, default=None):
        try:
            return self.getRegistry(key, default)
        except:
            return self.getRegistry(key)

    def setValue(self, key, value):
        self.setRegistry(key, value)

    def getVerifyFiles(self):
        return 1

    def getTestServerFlag(self):
        return self.testServerFlag

    def getGameServer(self):
        return self.getValue('GAME_SERVER')

    def getLogFileName(self):
        return 'toontown'

    def getPlayToken(self):
        if __debug__:
            token = self.getValue('LOGIN_TOKEN')
        else:
            try:
                token = sys.argv[1]
            except:
                token = ''
                return token
        return token

    def setRegistry(self, name, value):
        if not self.WIN32:
            return

        t = type(value)
        if t == types.IntType:
            WindowsRegistry.setIntValue(self.toontownRegistryKey, name, value)
        elif t == types.StringType:
            WindowsRegistry.setStringValue(self.toontownRegistryKey, name, value)
        else:
            self.notify.warning('setRegistry: Invalid type for registry value: ' + `value`)

    def getRegistry(self, name, missingValue=None):
        self.notify.info('getRegistry%s' % ((name, missingValue),))
        if not self.WIN32:
            if missingValue == None:
                missingValue = ''
            value = os.environ.get(name, missingValue)
            try:
                value = int(value)
            except: pass
            return value

        t = WindowsRegistry.getKeyType(self.toontownRegistryKey, name)
        if t == WindowsRegistry.TInt:
            if missingValue == None:
                missingValue = 0
            return WindowsRegistry.getIntValue(self.toontownRegistryKey,
                                                name, missingValue)
        elif t == WindowsRegistry.TString:
            if missingValue == None:
                missingValue = ''
            return WindowsRegistry.getStringValue(self.toontownRegistryKey,
                                                    name, missingValue)
        else:
            return missingValue

    def getCDDownloadPath(self, origPath, serverFilePath):
        return '%s/%s%s/CD_%d/%s' % (origPath, self.ServerVersion, self.ServerVersionSuffix, self.fromCD, serverFilePath)

    def getDownloadPath(self, origPath, serverFilePath):
        return '%s/%s%s/%s' % (origPath, self.ServerVersion, self.ServerVersionSuffix, serverFilePath)

    def getPercentPatchComplete(self, bytesWritten):
        if self.totalPatchDownload:
            return LauncherBase.getPercentPatchComplete(self, bytesWritten)
        else:
            return 0

    def hashIsValid(self, serverHash, hashStr):
        return serverHash.setFromDec(hashStr) or serverHash.setFromHex(hashStr)

    def launcherMessage(self, msg):
        LauncherBase.launcherMessage(self, msg)
        self.setRegistry(self.launcherMessageKey, msg)

    def getAccountServer(self):
        return self.accountServer

    def setTutorialComplete(self):
        self.setRegistry(self.tutorialCompleteKey, 0)

    def getTutorialComplete(self):
        return self.getRegistry(self.tutorialCompleteKey, 0)

    def getGame2Done(self):
        return self.getRegistry(self.game2DoneKey, 0)

    def setPandaErrorCode(self, code):
        self.pandaErrorCode = code
        if self.WIN32:
            self.notify.info('setting panda error code to %s' % code)
            exitCode2exitPage = {
                OTPLauncherGlobals.ExitEnableChat: 'chat',
                OTPLauncherGlobals.ExitSetParentPassword: 'setparentpassword',
                OTPLauncherGlobals.ExitPurchase: 'purchase'}
            if code in exitCode2exitPage:
                self.setRegistry('EXIT_PAGE', exitCode2exitPage[code])
                self.setRegistry(self.PandaErrorCodeKey, 0)
            else:
                self.setRegistry(self.PandaErrorCodeKey, code)
        else:
            LauncherBase.setPandaErrorCode(self, code)

    def getNeedPwForSecretKey(self):
        return self.secretNeedsParentPasswordKey

    def getParentPasswordSet(self):
        return self.chatEligibleKey

    def MakeNTFSFilesGlobalWriteable(self, pathToSet=None):
        if not self.WIN32:
            return
        LauncherBase.MakeNTFSFilesGlobalWriteable(self, pathToSet)

    def startGame(self):
        try:
            os.remove('Phase3.py')
        except: pass

        import Phase3

        self.newTaskManager()

        from direct.showbase.EventManagerGlobal import eventMgr
        eventMgr.restart()

        from toontown.toonbase import ToontownStart
