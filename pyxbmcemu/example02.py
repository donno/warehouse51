# python example
import xbmcgui

class TestWin(xbmcgui.Window): 
    def __init__(self):
        xbmcgui.Window.__init__(self)
        self.bg = xbmcgui.ControlImage(0,0,1280,720, 'background.png')
        self.addControl(self.bg)

W = TestWin() # create an instance of the Window
W.doModal()   # execute the loop
del W         # after the window is closed, Destroy it.
