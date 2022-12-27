# python example
import xbmcgui

# Tests
# These tests are for testing the angle for the ControlLabel

class TestWin(xbmcgui.Window):
    def __init__(self):
        xbmcgui.Window.__init__(self)
        BASE_Y = 720 / 3
        labels = []
        labels.append(xbmcgui.ControlLabel(200,BASE_Y,500,30, 'Quick brown fox jumped over lazy dog', angle = 0))
        labels.append(xbmcgui.ControlLabel(200,BASE_Y,500,30, 'Quick brown fox jumped over lazy dog', angle = 45))
        labels.append(xbmcgui.ControlLabel(200,BASE_Y,500,30, 'Quick brown fox jumped over lazy dog', angle = 90))
        labels.append(xbmcgui.ControlLabel(200,BASE_Y,500,30, 'Quick brown fox jumped over lazy dog', angle = 135))
        labels.append(xbmcgui.ControlLabel(200,BASE_Y,500,30, 'Quick brown fox jumped over lazy dog', angle = 180))
        labels.append(xbmcgui.ControlLabel(200,BASE_Y,500,30, 'Quick brown fox jumped over lazy dog', angle = 225))
        labels.append(xbmcgui.ControlLabel(200,BASE_Y,500,30, 'Quick brown fox jumped over lazy dog', angle = 270))
        labels.append(xbmcgui.ControlLabel(200,BASE_Y,500,30, 'Quick brown fox jumped over lazy dog', angle = 315))
        labels.append(xbmcgui.ControlLabel(200,BASE_Y,500,30, 'Quick brown fox jumped over lazy dog', angle = 360))

        for l in labels:
            self.addControl(l)

W = TestWin() # create an instance of the Window
W.doModal()   # execute the loop
del W         # after the window is closed, Destroy it.
