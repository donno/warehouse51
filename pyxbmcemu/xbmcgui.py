"""
    xbmcgui.py - Emulator for XBMC Media Center
"""

__author__  = 'darkdonno'
__credits__ = 'Team XBMC'
__date__    = 'November 2009'
__version__ = '0.1-git'

# CONSTANTS
ICON_OVERLAY_HAS_TRAINER = 4
ICON_OVERLAY_HD = 8
ICON_OVERLAY_LOCKED = 3
ICON_OVERLAY_NONE = 0
ICON_OVERLAY_RAR = 1
ICON_OVERLAY_TRAINED = 5
ICON_OVERLAY_UNWATCHED = 6
ICON_OVERLAY_WATCHED = 7
ICON_OVERLAY_ZIP = 2

# Emulator Varibles
currentWindowDialogId = -1
currentWindowDialog   = None

import pygame
from pygame.locals import *

Emulating = True

# Classes
class Action:
    def getAmount1():
        return -1

    def getAmount2():
        return -1

    def getButtonCode():
        return -1

    def getId():
        return 0

class Control:
    baseID = 0
    def __init__(self):
        self.id = Control.baseID
        Control.baseID = Control.baseID + 1
        self.width  = 0
        self.height = 0
        self.x = 0
        self.y = 0
        self.enable = True
        self.visible = True
        self.controlup    = None
        self.controldown  = None
        self.controlleft  = None
        self.controlright = None

    def controlDown( self, control):
        self.controldown  = control
    def controlLeft( self, control):
        self.controlleft  = control
    def controlRight( self, control):
        self.controlright = control
    def controlUp( self, control):
        self.controlup    = control

    def getHeight( self ):
        return self.height
    def getWidth( self ):
        return self.width

    #def setAnimations(self, event, attr

    def setEnableCondition(self, enable):
        # LOTS OF WORK to implement
        self.enablecondition = enable

    def setEnabled( self, enabled ):
        self.enable = enabled

    def setHeight( self, height ):
        self.height = height

    def setNavigation(self, up, down, left, right):
        self.controlup    = up
        self.controldown  = down
        self.controlleft  = left
        self.controlright = right

    def setPosition( self, x, y):
        self.x = x
        self.y = y

    def setVisible( self, visible):
        self.visible = visible

    def setVisibleCondition( self, visible,allowHiddenFocus=True):
        # LOTS OF WORK to implement
        pass

    def setWidth( self, width ):
        self.width = width

    def emu_render( self , screen ):
        pass

class ControlImage(Control):
    # Notes: colorKey, aspectRatio and colorDiffuse is unsued
    def __init__( self, x, y, width, height, filename, colorKey='0xFFFF3300', aspectRatio=0, colorDiffuse='0xC0FF0000' ):
        Control.__init__(self)
        self.setPosition( x , y )
        self.setWidth( width )
        self.setHeight( height )
        self.image = pygame.image.load(filename)
        self.colorKey = colorKey
        self.aspectRatio  = 0
        self.colorDiffuse = colorDiffuse

    def setColorDiffuse(self, colorDiffuse):
        self.colorDiffuse = colorDiffuse

    def setImage( self, filename ):
        self.image = pygame.image.load(filename)

    def emu_render( self , screen ):
        if not self.visible:
            return

        screen.blit(self.image, ( self.x, self.y, self.getWidth(), self.getHeight()))

class ControlLabel(Control):
    def __init__(self, x, y, width, height, label, font = 'font13', textColor = '0xFFFFFFFF', disabledColor='0xFFFF3300', alignment = 0, hasPath=False, angle = 0):
        Control.__init__(self)
        self.setPosition( x , y )
        self.setWidth( width )
        self.setHeight( height )
        # Label specific
        self.label     = label
        self.font      = font
        self.textColor = textColor
        self.disaColor = disabledColor
        self.alignment = alignment
        self.hasPath   = hasPath
        self.angle     = angle

        # ignore font for now
        self.emu_font = pygame.font.Font(None, 24)
        self.emuint_render()

    def getLabel(self):
        return self.label

    def setLabel(self, label):
        self.label = label
        self.emuint_render()

    def emuint_render( self ):
        self.emu_text = self.emu_font.render(self.label, 1, pygame.Color(self.textColor))
        self.emu_text_disabled = self.emu_font.render(self.label, 1, pygame.Color(self.disaColor))

        if self.emu_text.get_width() > self.width:
            # Crop it
            self.emu_text = self.emu_text.subsurface((0,0, self.width, self.emu_text.get_height()))
            self.emu_text_disabled = self.emu_text_disabled.subsurface((0,0, self.width, self.emu_text_disabled.get_height()))

        #print dir(self.emu_text)
        if self.angle != 0:
            self.emu_text = pygame.transform.rotate(self.emu_text, self.angle)
            self.emu_text_disabled = pygame.transform.rotate(self.emu_text_disabled, self.angle)

    def emu_render( self , screen ):
        if not self.visible:
            return

        # if angle modifier x and y
        position = None
        if (self.alignment == 0): # left
            position = (self.x, self.y)
        elif (self.alignment == 1): # right
            textwidth = self.emu_text.get_rect().w
            #position = (self.x + self.getWidth() - textwidth, self.y)
            position = (self.x - textwidth, self.y)
            # Tested against XBMC :| does this effect
        elif (self.alignment == 2): # center
            textwidth = self.emu_text.get_rect().w / 2.0
            position = (self.x + (self.getWidth() / 2.0 - textwidth), self.y)
        else:
            print "ERROR: ControlLabel - Alignment not handled"
            position = (0, 0)

        if self.angle != 0:
            #print "angle"
            pass
        if self.enable:
            screen.blit(self.emu_text, position)
        else:
            screen.blit(self.emu_text_disabled, position)

class Window:
    _WIDTH_  = 1280 # Emu only
    _HEIGHT_ = 720  # Emu only

    def __init__(self, windowId=1):
        pygame.init()
        self.screen = pygame.display.set_mode(
                        (self.getWidth(), self.getHeight()))

        pygame.display.set_caption('XBMC / Emulated Window')
        self.bClose = False
        self.focus = None
        self.controls = []
        self.viewChange = False
        #pygame.mouse.set_visible(False)

    def addControl(self, control):
        if (control == None):
            return

        self.controls.append(control)
        self.viewChange = True

    def clearProperties(self):
        pass

    def clearProperty(self, key):
        pass

    def close(self):
        self.bClose = True

    def doModal(self):
        while not self.bClose:
            # Renderer
            if (self.viewChange):
                self.screen.fill((0, 0, 0))
                for control in self.controls:
                    control.emu_render( self.screen )
                #self.viewChange = False
                pygame.display.flip()
            # Event Loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()

    def getControl(self, controlId):
        return None

    def getFocus(self):
        return self.focus

    def getFocusId(self):
        if (self.focus is None):
            return -1
        return self.focus.getId()

    def getHeight(self):
        return self._HEIGHT_

    def getProperty(key):
        return None

    def getResolution(self):
        """
        0 - 1080i      (1920x1080)
        1 - 720p       (1280x720)
        2 - 480p 4:3   (720x480)
        3 - 480p 16:9  (720x480)
        4 - NTSC 4:3   (720x480)
        5 - NTSC 16:9  (720x480)
        6 - PAL 4:3    (720x576)
        7 - PAL 16:9   (720x576)
        8 - PAL60 4:3  (720x480)
        9 - PAL60 16:9 (720x480)
        """
        return 1

    def getWidth(self):
        return self._WIDTH_

    def onAction(self, action):
        pass

    def removeControl(self, control):
        if control in self.controls:
            self.controls.remove(control)
        self.viewChange = True

    def setCoordinateResolution(self, resolution):
        pass

    def setFocus(self, Control):
        pass

    def setFocusId(self, int):
        pass

    def setProperty(key, value):
        pass

    def show():
        pass

class Dialog:
    def ok(heading, line1, line2=None, line3=None):
        print ":NYI:"
        print "Dialog().ok(%s, %s, %s, %s)"% (heading, line1, line2, line3)

# Functions
def getCurrentWindowDialogId():
    return currentWindowDialogId

def getCurrentWindowDialog():
    return currentWindowDialog

def lock():
    pass

def unlock():
    pass
