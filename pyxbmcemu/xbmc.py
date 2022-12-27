"""
    xbmc.py - Emulator for XBMC Media Center
"""

__author__  = 'darkdonno'
__credits__ = 'Team XBMC'
__date__    = 'November 2009'
__version__ = '0.1-git'

# Emulator Option Structure
class EmulatorStruct:
    freeMem = 0xBEEF
    logFile = None
    def LevelToString(self, level):
        # prefix:
        prefix = ""
        if level == LOGDEBUG:       #0
            prefix = "LOGDEBUG: "
        elif level == LOGINFO:      #1
            prefix = "LOGINFO: "
        elif level == LOGNOTICE:    #2
            prefix = "LOGNOTICE: "
        elif level == LOGWARNING:   #3
            prefix = "LOGWARNING: "
        elif level == LOGERROR:     #4
            prefix = "LOGERROR: "
        elif level == LOGSEVERE:    #5
            prefix = "LOGSEVERE: "
        elif level == LOGNONE:      #7
            prefix = "LOGNONE: "
        return prefix

# Constants
DRIVE_NOT_READY = 1
LOGDEBUG = 0
LOGERROR = 4
LOGFATAL = 6
LOGINFO = 1
LOGNONE = 7
LOGNOTICE = 2
LOGSEVERE = 5
LOGWARNING = 3
PLAYER_CORE_AUTO = 0
PLAYER_CORE_DVDPLAYER = 1
PLAYER_CORE_MPLAYER = 2
PLAYER_CORE_PAPLAYER = 3
PLAYLIST_MUSIC = 0
PLAYLIST_VIDEO = 1
TRAY_CLOSED_MEDIA_PRESENT = 96
TRAY_CLOSED_NO_MEDIA = 64
TRAY_OPEN = 16

# classes
"""
class InfoTagMusic:
    def getAlbum():
        return "Album"
    def getDisc():
        return "Disc"
    def getDuration():
        return "Duration"
    def getAlbum():
        return "Album"
    def getReleaseDate():
        return "ReleaseDate"
    def getTitle():
        return "Title"
    def getTrack():
        return "Track"
    def getURL():
        return "Url"
"""


# function calls
def dashboard():
    print "xbmc.dashboard() called - returning to dashboad (os)"
    from sys import exit
    exit(0)

def enableNavSounds(yesNo):
    pass

def executebuiltin(function):
    pass

def executehttpapi(httpcommand):
    pass

def executescript(script):
    pass

def getCacheThumbName(path):
    pass

def getCondVisibility(condition):
    pass

def getDVDState():
    pass

def getFreeMem():
    return EmulatorStruct.freeMem

def getGlobalIdleTime():
    pass

def getIPAddress():
    # Note: May return be IPv6
    from socket import gethostbyaddr, gethostname
    return gethostbyaddr(gethostname())[2][0]

def getInfoImage(infotag):
    pass

def getInfoLabel(infotag):
    pass

def getLocalizedString(id):
    pass

def getRegion(id):
    pass

def getSkinDir():
    pass

def getSupportedMedia(media):
    pass

def log(msg, level=LOGNOTICE):
    if EmulatorStruct.logFile is None:
        EmulatorStruct.logFile = open( "xbmcemu.log" , "wa" )
    prefix = EmulatorStruct().LevelToString(level)
    EmulatorStruct.logFile.write(prefix + msg)

def makeLegalFilename(filename, fatX=True):
    pass

def output(msg, level=LOGNOTICE):
    prefix = EmulatorStruct().LevelToString(level)
    log(msg, level)
    print prefix + msg

def playSFX(filename):
    pass

def restart():
    ## TODO: Improve this to Close the script then re run it.
    print "xbmc.shutdown() called - closing just python"
    from sys import exit
    exit(0)

def shutdown():
    print "xbmc.shutdown() called - closing just python"
    from sys import exit
    exit(0)

def skinHasImage(image):
    pass

def sleep(time):
    pass

def translatePath(path):
    pass

