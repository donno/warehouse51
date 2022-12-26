import math

class SVGLeveler:
    base_svg_top = """<?xml version="1.0"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" width="%i" height="%i">"""
    base_svg_bottom = """</svg>"""

    def __init__(this, width, height, initalRadius, levels=3):
        this.width = width
        this.height = height
        this.body = []
        this.baseCircleR = initalRadius
        this.levels = levels
        this.drawBaseLevelCircles(initalRadius, levels)

    def drawBaseLevelCircles(this, initalRadius, levels=3):
        x = this.width / 2.0
        y = this.height / 2.0
        initalRadius * levels
        this.baseCircleR = initalRadius
        for i in xrange(1, levels+1):
            r = initalRadius * (levels+1- i)
            col = "rgb(%i,0,0)" % (255-((levels- i)/(levels+0.0)*255))
            this.addCircle(x,y,r, fill=col)

    def addCircle(this, x, y, r, fill="gray"):
        this.body.append('<circle cx="%i" cy="%i" r="%i" fill="%s" stroke="black" stroke-width="5"  />' % (x,y,r, fill))

    def addLine(this, x1,y1, x2, y2):
        this.body.append('<line x1="%i" y1="%i" x2="%i" y2="%i" stroke="black" stroke-width="2"/>' % (x1,y1, x2,y2))

    def writeTextLevel(this, level, text):
        center = this.getCenter()
        if (level == 0):
            pnt = center
        else:
            pnt = (0,0)
        this.addText(pnt[0],pnt[1],text)

    def addText(this, x, y, text):
        this.body.append('<text x="%i" y="%i" text-anchor="middle" fill="white" font-size="15">%s</text>' % (x,y,text))

    def addItemsAtLevel(this, level, items):
        if (level == 0):
            return

        numberSections = len(items)
        center = this.getCenter()
        eachSectAngle = math.pi*2 / numberSections
        print eachSectAngle
        for i in xrange(0, numberSections):
            this.addLineSpec(center[0]+this.baseCircleR*level*math.cos(eachSectAngle*i),center[1]+this.baseCircleR*level*math.sin(eachSectAngle*i), i*eachSectAngle )
            x  = 400
            y = 400
            #this.body.append('<text x="%i" y="%i" text-anchor="middle" fill="white" font-size="15">%s</text>' % (x,y,items[i]))
        

    def addLineSpec(this, x, y, angle):
        this.addLine(x, y, x+this.baseCircleR*math.cos(angle), y+this.baseCircleR*math.sin(angle))

    def getCenter(this):
        return (this.width / 2.0, this.height / 2.0)

    def printDoc(this):
        print SVGLeveler.base_svg_top % (this.width,this.height)
        for entry in this.body:
            print entry
        print SVGLeveler.base_svg_bottom

d =  SVGLeveler(800,800, 100, 3)
d.writeTextLevel(0, "hello")
d.addItemsAtLevel(1,["foo","bar","far","bar"])
d.printDoc()

