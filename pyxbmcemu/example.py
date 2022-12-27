# python example
import xbmcgui

class TestWin(xbmcgui.Window): 
    def __init__(self):
        xbmcgui.Window.__init__(self)
        pass  # Constructor - do nothing

W = TestWin() # create an instance of the Window
W.doModal()   # execute the loop
del W         # after the window is closed, Destroy it.
