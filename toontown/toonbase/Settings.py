from panda3d.core import *

class Settings:
    def __init__(self):
        self.mode = None
        self.music = None
        self.sfx = None
        self.toonChatSounds = None
        self.musicVol = None
        self.sfxVol = None
    
    def readSettings(self):
        self.mode = ConfigVariableBool('fullscreen')
        self.music = ConfigVariableBool('audio-music-active')
        self.sfx = ConfigVariableBool('audio-sfx-active')
        self.toonChatSounds = ConfigVariableBool('toon-chat-sounds')
        self.musicVol = ConfigVariableDouble("audio-master-music-volume") / 100.0
        self.sfxVol = ConfigVariableDouble("audio-master-sfx-volume") / 100.0
        #mode = not Settings.getWindowedMode()
        #music = Settings.getMusic()
        #sfx = Settings.getSfx()
        #toonChatSounds = Settings.getToonChatSounds()
        #musicVol = Settings.getMusicVolume()
        #sfxVol = Settings.getSfxVolume()"""

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