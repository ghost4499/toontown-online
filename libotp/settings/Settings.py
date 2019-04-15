from panda3d.core import *
import sys

class Settings:
    def __init__(self):
        self.mode = None
        self.music = None
        self.sfx = None
        self.toonChatSounds = None
        self.musicVol = None
        self.sfxVol = None

        self.res = None
    
    def readSettings(self):
        self.mode = base.config.GetBool('fullscreen')
        self.music = base.config.GetBool('audio-music-active')
        self.sfx = base.config.GetBool('audio-sfx-active')
        self.toonChatSounds = base.config.GetBool('toon-chat-sounds')
        self.musicVol = base.config.GetDouble("audio-master-music-volume")
        self.sfxVol = base.config.GetDouble("audio-master-sfx-volume")

    def getWindowedMode(self):
        return self.mode

    def getMusic(self):
        return self.music

    def getSfx(self):
        return self.sfx

    def getToonChatSounds(self):
        return self.toonChatSounds

    def getMusicVolume(self):
        return self.musicVol

    def getSfxVolume(self):
        return self.sfxVol
    
    def getAvailableResolutions(self):
        di = base.pipe.getDisplayInformation()
        sizes = []
        for i in range(di.getTotalDisplayModes()):
              sizes += [(di.getDisplayModeWidth(i), di.getDisplayModeHeight(i))]
        print(sizes)
        return sizes

    def getDisplayInformation(self):
        if sys.platform == 'win32':
            import ctypes
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware() # Set the window as DPI Aware
            self.setResolution(user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
    
    def setResolution(self, width, height):
        self.res = (width, height)
    
    def getResolution(self):
        return self.res
