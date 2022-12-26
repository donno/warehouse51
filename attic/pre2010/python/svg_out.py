import math

class SVGDoc:
    base_svg_top = """<?xml version="1.0"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" width="%i" height="%i">"""
    base_svg_bottom = """</svg>"""

    def __init__(this, width, height):
        this.width = width
        this.height = height
        this.body = []
        this.baseCircleR = 0
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

    def addArc(this, x, y, r, outR,  startAngle, endAngle):
        # A = elliptical Arc
        #250 150 with a line to position 150 350 then from there a line to 350 350 and finally closing the path back to 250 150.
        #(rx ry x-axis-rotation large-arc-flag sweep-flag x y)
        #Mx,y  << means move to   v = vertical lineto
        
        
        #(rx ry x-axis-rotation large-arc-flag sweep-flag x y)
        # Starting Point is at startAngle on the a distancae r from x,y 
        # therefore if startangle = 0,0,    y = y,  x = r 

        # inner X 
        
        #<path d="M 288,288 L 356.58385,291.71732 C 346.90219,370.84511 307.32064,426.05299 230.31478,451.32142 L 201.02036,380.61074 C 245.04317,367.08514 271.47762,337.22748 277.79195,288.68686 z " />

        startX_inner = x + r * math.cos(startAngle)
        startY_inner = y + r * math.sin(startAngle)

        startX_outer = x + (r + outR) * math.cos(startAngle)
        startY_outer = y + (r + outR) * math.sin(startAngle)
        
        endX_inner = x + r * math.cos(endAngle)
        endY_inner = y + r * math.sin(endAngle)

        endX_outer = x + (r + outR) * math.cos(endAngle)
        endY_outer = y + (r + outR) * math.sin(endAngle)

        sip = "%i,%i" % ( startX_inner , startY_inner )
        sop = "%i,%i" % ( startX_outer , startY_outer )

        print sip
        print sop
        #print "M %s C%i %i %i %i" % (sip, sop)
        print '<circle cx="%d" cy="%d" r="10" />' % ( startX_inner , startY_inner )
        print '<circle cx="%d" cy="%d" r="10" />' % ( startX_outer , startY_outer )
        print '<circle cx="%d" cy="%d" r="10" />' % ( endX_inner , endY_inner )
        print '<circle cx="%d" cy="%d" r="10" />' % ( endX_outer , endY_outer )
        pathData = "M %d,%d L %d,%d L %d,%d" % (startX_inner , startY_inner, startX_outer , startY_outer, endX_outer , endY_outer ) # so far draws a line from start to outer
        print '<path d="%s" />' % pathData

        #(x1 y1 x2 y2 x y)+

        #this.body.append('<path d="M%i,%i L300,100 A%i,%i 0 0,0 %i,%i" fill="yellow" stroke="black" stroke-width="5"  />' % (x,y,startX,startY,endX, endY))
        #print '<path d="M %i,%i L 356.58385,291.71732 C 346.90219,370.84511 307.32064,426.05299 230.31478,451.32142 L 201.02036,380.61074 C 245.04317,367.08514 271.47762,337.22748 277.79195,288.68686 z " />' % (x,y)
        
        #                  <path d="M300,200 v-150 a100,100,0,0,0,-100,100 z" fill="yellow" stroke="black" stroke-width="5"  />
        #<path d="M300,200 L300,100 A200,200 0 0,1 400,200 z" />
        
        print startX_inner

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
        else:
            print level
        numberSections = len(items)
        
        print numberSections
        center = this.getCenter()
        baseX = center[0]+this.baseCircleR
        baseY = center[1]
        
        
        nextX 
        
        this.addLine(baseX, baseY baseX*, baseY)
        
    def getCenter(this):
        return (this.width / 2.0, this.height / 2.0)
    def printDoc(this):
        print SVGDoc.base_svg_top % (this.width,this.height)
        for entry in this.body:
            print entry
        print SVGDoc.base_svg_bottom

""""
  <circle cx="300" cy="200" r="100" fill="maroon" stroke="black" stroke-width="5"  />
  <text x="200" y="150" fill="blue" > Movie 1 (tt112345)</text>
  <path d="M275,175 v-150 a150,150 0 0,0 -150,150 z"
        fill="yellow" stroke="blue" stroke-width="5" />
"""
d =  SVGDoc(800,800)
d.drawBaseLevelCircles(100,3)
d.writeTextLevel(0, "hello")
d.addItemsAtLevel(1,["foo","bar","far"])
d.printDoc()

