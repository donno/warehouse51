# python example
import xbmcgui

# Tests
#  hw1 = generic test - left aligned
#  hw2 = aligned right
#  hw3 = aligned centre
#  hw4= test setVisible
#  hw5 = test setLabel
#  hw6 = test label bounding/cropping
#  hw6 = test label bounding/cropping
#  hw7 = test angle

class TestWin(xbmcgui.Window):
    def __init__(self):
        xbmcgui.Window.__init__(self)
        BASE_Y = 720 / 3
        self.bg = xbmcgui.ControlImage(0,0,1280,720, 'background.png')
        self.hw1 = xbmcgui.ControlLabel(200,BASE_Y,500,30, 'Hello World!')
        self.hw2 = xbmcgui.ControlLabel(200,BASE_Y+30,500,30, 'Hello Right!' , alignment = 1 )
        self.hw3 = xbmcgui.ControlLabel(200,BASE_Y+60,500,30, 'Hello Centre!', alignment = 2 )
        self.hw4 = xbmcgui.ControlLabel(200,BASE_Y + 50,500,30, 'Test setVisible(false) - I should be hidden')
        self.hw5 = xbmcgui.ControlLabel(200,BASE_Y + 100,500,30, 'This text should just say foobar')
        self.hw6 = xbmcgui.ControlLabel(200,BASE_Y + 140,400,30, 'This should be disabled')
        self.hw7 = xbmcgui.ControlLabel(200,BASE_Y + 190,400,30, 'This text should be cut short, 12345678901234567890')
        self.hw8 = xbmcgui.ControlLabel(200,BASE_Y + 210,500,30, 'This text should be rotated 45 degrees', angle = 45)

        self.addControl(self.bg)
        self.addControl(self.hw1)
        self.addControl(self.hw2)
        self.addControl(self.hw3)
        self.addControl(self.hw4)
        self.addControl(self.hw5)
        self.addControl(self.hw6)
        self.addControl(self.hw7)
        self.addControl(self.hw8)

        self.hw4.setVisible(False)
        self.hw5.setLabel("foobar")
        self.hw6.setEnabled(False)
        print "Test %s | GetLabel Test 1" % ( self.hw1.getLabel() == 'Hello World!')
        print "Test %s | GetLabel Test 2" % ( self.hw5.getLabel() == 'foobar')

W = TestWin() # create an instance of the Window
W.doModal()   # execute the loop
del W         # after the window is closed, Destroy it.
