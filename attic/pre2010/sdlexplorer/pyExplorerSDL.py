import os, sys
import pygame
from pygame.locals import *

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'

__title__ = "pyExplorer"
__author__ = "Donno"

class FileDirEntry:
    def __init__(this, name, type, size):
        this.name = name
        this.type = type
        this.size = size
    def p(this):
        print "%25s    [%s]    %i bytes" % (this.name, this.type, this.size)

class Button:
    def __init__(this, id, pos, size, text, textureFocus, textureNoFocus, font, textColor = (255,255,255)):
        this.position = pos
        this.id   = id
        this.size = size
        this.text = text
        this.font = font
        this.surfaceText    = font.render(text, 1, textColor)
        this.textureFocus   = pygame.transform.scale(textureFocus,size)
        this.textureNoFocus = pygame.transform.scale(textureNoFocus,size)
        this.hasFocus   = 0
        this.textOffset = (15,10)
        this.up    = None
        this.right = None
        this.left  = None
        this.down  = None

    def Render(this, surface):
        if (this.hasFocus == 0):
            surface.blit(this.textureNoFocus, this.position)
        else:
            surface.blit(this.textureFocus, this.position)
        surface.blit(this.surfaceText, (this.position[0] + this.textOffset[0], this.position[1] + this.textOffset[1]))

    def SetNavigation(this, left, right, up, down):
        this.up    = up
        this.right = right
        this.left  = left
        this.down  = down

    #def Click(this):
    #    print "Clicked"

class List:
    """
        'Premodded list for file items'
    """
    def __init__(this, pos, size, textureFocus, textureNoFocus, font, textColor = (255,255,255)):
        this.pos = pos
        this.size = size
        this.textureFocus = textureFocus
        this.textureNoFocus = textureNoFocus
        this.font = font
        this.textColor = textColor
        this.items = []
        this.icons = {}
        this.selectedItemNumber = 0
        this.itemheight = 32
        this.thumbSize = 32
        this.showThumb = 1

    def SetIcon(this, iconName, iconSurface):
        this.icons[iconName] = iconSurface

    def AddItem(this, FileItem):
        this.items.append(FileItem)

    def Render(this, surface):
        posy = this.pos[1]
        if (this.showThumb):
            iconDir = pygame.transform.scale(this.icons['folder'], (this.thumbSize, this.thumbSize))
            iconFile = pygame.transform.scale(this.icons['file'], (this.thumbSize, this.thumbSize))

        for item in this.items:
            if (posy + this.itemheight < 576):
                itemSurfLabel1 = this.font.render(item.name, 1, this.textColor)
                if (this.showThumb):
                    if (item.type == 'D'):
                        surface.blit(iconDir, (this.pos[0], posy))
                    elif (item.type == 'F'):
                        #surface.blit(iconFile, (this.pos[0], posy))
                        pass
                    surface.blit(itemSurfLabel1, (this.pos[0] + this.thumbSize + 15, posy))
                else:
                    surface.blit(itemSurfLabel1, (this.pos[0], posy))
                #this.thumbSize
                posy = posy + this.itemheight
        #this.surfaceText = font.render(text, 1, textColor)
        #if (this.hasFocus == 0):
        #    surface.blit(this.textureNoFocus, this.position)
        #else:
        #    surface.blit(this.textureFocus, this.position)

        #surface.blit(this.surfaceText, (this.position[0] + this.textOffset[0], this.position[1] + this.textOffset[1]))

class PyExplorerMain:
    """The Main PyExplorer Class - This class handles the main initialization and creating of the Explorer."""
    def __init__(self, width=720,height=576):
        pygame.init()
        pygame.font.init()
        self.listType = 1
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(__title__)
        self.headingFont = pygame.font.Font(pygame.font.get_default_font(), 35)
        self.mainFont = pygame.font.Font(pygame.font.get_default_font(),14)
        self.bgSurface = pygame.image.load("images/background.png").convert()
        self.surfaceButtonFocus = pygame.image.load("images/button-focus.png").convert()
        self.surfaceButtonNoFocus = pygame.image.load("images/button-nofocus.png").convert()
        self.bgSurface = pygame.image.load("images/background.png").convert()
        sTitle = self.headingFont.render(__title__, 1, (255,255,255))
        textpos = sTitle.get_rect(top=10,centerx=self.bgSurface.get_width()/2)
        self.bgSurface.blit(sTitle, textpos)
        # Title is now embeded in BG
        self.dir = "F:/"
        self.screen.blit(self.bgSurface, (0,0))
        self.screen.blit(self.mainFont.render("Path: " + self.dir, 1, (255,255,255)), (25,60))

        bs = (84,28)
        self.buttons = []

        self.buttons.append(Button(1, ( 0  ,0),bs, "File" , self.surfaceButtonFocus, self.surfaceButtonNoFocus, self.mainFont))
        self.buttons.append(Button(2, (bs[0],0),bs, "Edit" , self.surfaceButtonFocus, self.surfaceButtonNoFocus, self.mainFont))
        self.buttons.append(Button(3, (bs[0]*2,0),bs, "View" , self.surfaceButtonFocus, self.surfaceButtonNoFocus, self.mainFont))
        #self.buttons.append(Button(4, (bs[0]*3,0),bs, "Tools", self.surfaceButtonFocus, self.surfaceButtonNoFocus, self.mainFont))
        #self.buttons.append(Button(5, (bs[0]*4,0),bs, "Help" , self.surfaceButtonFocus, self.surfaceButtonNoFocus, self.mainFont))
        self.buttons.append(Button(4, (720-bs[0]*2,0),bs, "Tools", self.surfaceButtonFocus, self.surfaceButtonNoFocus, self.mainFont))
        self.buttons.append(Button(5, (720-bs[0],0),bs, "Help" , self.surfaceButtonFocus, self.surfaceButtonNoFocus, self.mainFont))

        self.buttons[0].hasFocus = 1
        self.ctrlFocus = self.buttons[0]

        #print "Number of Buttons: %i" % len(self.buttons)
        for i in xrange(0, len(self.buttons)):
            if (i == 0):
                self.buttons[i].SetNavigation(self.buttons[len(self.buttons)-1],self.buttons[i+1],None,None)
            elif (i == 4):
                self.buttons[i].SetNavigation(self.buttons[i-1],self.buttons[0],None,None)
            else:
                self.buttons[i].SetNavigation(self.buttons[i-1],self.buttons[i+1],None,None)

        self.fileList = List((15, 95),(720-15*2,576-95-15),self.surfaceButtonFocus,None,self.mainFont)
        self.fileList.SetIcon("folder", pygame.image.load("images/DefaultFolderBig.png"))
        self.fileList.SetIcon("file", pygame.image.load("images/DefaultFileBig.png"))


        folderList = listFolder(self.dir)
        for item in folderList:
            self.fileList.AddItem(item)


        self.RenderWindow()
        #it__(this, pos, size, textureFocus, textureNoFocus, font, textColor = (255,255,255)):
        #self.screen.blit(self.surfaceTitle, (0,0))
        #self.RenderCWD()
        pygame.display.flip()

    def RenderWindow(self):
        for b in self.buttons:
            b.Render(self.screen)
        self.fileList.Render(self.screen)
        pygame.display.flip()

    def RenderCWD(self):
        folderList = listFolder(self.dir)
        self.RenderFolderList(folderList)

    def RenderFolderList(self, folderList):
        if (self.listType == 1):
            posy = 95
            for item in folderList:
                self.screen.blit(self.mainFont.render(item.name, 1, (255,255,255)), (25,posy))
                posy = posy + 25

    def MainLoop(self):
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif (event.type == pygame.KEYUP):
                    if (event.key == 13):
                        self.ControlClicked(self.ctrlFocus.id)
                    elif (event.key == 275):
                        if (self.ctrlFocus.right is not None):
                            self.SetFocus(self.ctrlFocus.right)
                    elif (event.key == 276):
                        if (self.ctrlFocus.left is not None):
                            self.SetFocus(self.ctrlFocus.left)
                    else:
                        print event.key
                elif (event.type == pygame.MOUSEBUTTONUP):
                    if (event.button == 1):
                        b = self.CheckCtrl(event.pos)
                        if b is not None:
                            self.ControlClicked(b.id)
                elif (event.type == pygame.MOUSEMOTION):
                        b = self.CheckCtrl(event.pos)
                        if (b != self.ctrlFocus and b is not None):
                            self.SetFocus(b)

    def SetFocus(self, newCtrl):
        self.ctrlFocus.hasFocus = 0
        newCtrl.hasFocus = 1
        self.ctrlFocus = newCtrl
        self.RenderWindow()

    def CheckCtrl(self,pos):
        x = pos[0]
        y = pos[1]
        for b in self.buttons:
            if (x <= b.position[0] + b.size[0] and x >= b.position[0]):
                if (y <= b.position[1] + b.size[1] and y >= b.position[1]):
                    return b
        return None

    def ControlClicked(this, controlID):
        if (controlID == 1):
            print "FILE"

def listFolder(folderPath):
    fileDirList = []
    dirList=os.listdir(folderPath)
    for fname in dirList:
        fullPath = os.path.join(folderPath,fname)
        if os.path.isdir(fullPath):
            fileDirList.append(FileDirEntry(fname,'D',0))
        elif os.path.isfile(fullPath):
            fileDirList.append(FileDirEntry(fname,'F', os.path.getsize(fullPath)))
        else:
            fileDirList.append(FileDirEntry(fname,'U', os.path.getsize(fullPath)))
    return fileDirList

if __name__ == "__main__":
    pyMainEx = PyExplorerMain()
    pyMainEx.MainLoop()
