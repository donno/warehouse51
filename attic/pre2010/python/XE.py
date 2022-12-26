# 
# Author: Donno
# Code Copyright 2006 Donno [donno45989@yahoo.com.au]
#
# Multi Purpose
# X-Chat, System (run with CMD line), possibley XBMC

# About X-Chat
# Private Usage Only (eg /XE      (should work same as CMD) (note this can be done another way

# Using in X-Chat for Private Usage only
# add the following to the User Commands
#       Name= XE   Command= exec python D:\XE.py &2


# INFO About Country Code 
#    http://www.xe.com/iso4217.htm
#    Possible for add a option to be able to list contry codes etc


# Next 3 lines are pretty much for X-Chat only
__module_name__ = "XE.Com Converter" 
__module_version__ = "1.0" 
__module_description__ = "Converts Currenancy" 

import urllib,re,sys
Base_URL = "http://www.xe.com/ucc/convert.cgi"
CC_URL = "http://www.xe.com/iso4217.htm"  # Contry Code URL

# MODES,  0 == CMD Line,    1 == X-Chat,  2 == XBMC (if i do XBMC)
MODE = 0
if MODE == 1:
    import xchat
elif MODE == 2:
    import xbmcgui,xbmc

def doConverstion(Amout,From,To):
    txdata  = urllib.urlencode( {'Amount':Amout, 'From':From, 'To':To} )
    html=urllib.urlopen(Base_URL,txdata).read()
    nfo = re.compile('<tr valign=middle>\n.*<td width=49% align=right style="font-family:Arial,Helvetica; font-size:10pt; color:#000000;">\n.*<span style="font-size:14pt; font-weight:bold;">(.*)</span><br>.*\n.*</td>\n    <td width= 2% align=center style="font-family:Arial,Helvetica; font-size:24pt; font-weight:bold; color:#000000;">=</td>\n    <td width=49% align=left style="font-family:Arial,Helvetica; font-size:10pt; color:#000000;">\n      <span style="font-size:14pt; font-weight:bold;">(.*)</span><br>', re.IGNORECASE).findall(html)[0]
    return str(nfo[0]) + " = " + str(nfo[1])
    
def getCountryCodes(ntyp=None):
    html=urllib.urlopen(CC_URL).read()
    nfo = re.compile('<TR BGCOLOR=#.*><TD><TT>(.*)</TT></TD><TD><TT>(.*)</TT></TD></TR>', re.IGNORECASE).findall(html)
    ccnfo,cc_3dig,cn = [],"",0
    for n in nfo:
        ccnfo.append(n[0] + "     " + n[1])
        cc_3dig += n[0] +  "    "
        cn +=1
        if cn == 14:
            cn = 0
            cc_3dig += "\n"
    if ntyp == 1: return cc_3dig
    else: return ccnfo
        
def hook_xe():
    # X-Chat Function 
    pass
## CODE HERE TO LOAD sys.argb (eg for Windows/Linux/Pc cmd line usage
if MODE == 0:
    if len(sys.argv) == 4:
        Amout = sys.argv[1]
        From = sys.argv[2]
        To = sys.argv[3]
        print doConverstion(Amout,From,To)
    elif len(sys.argv) == 2:
        if sys.argv[1].lower() == "help":
            print "USAGE: \nXE.py Amount From TO \nXE.py listcodes \nXE.py list3cc"
        if sys.argv[1].lower() == "listcodes":
            cc = getCountryCodes()
            for i in cc:
                print i
        if sys.argv[1].lower() == "list3cc":
            cc = getCountryCodes(1)
            print cc
            """
            dd,n = "",0
            for i in cc:
                dd += i +  "    "
                n +=1
                if n == 14:
                    n = 0
                    dd += "\n"
            #print dd
            """
    else:
        print "USAGE: \nXE.py Amount From TO \nXE.py listcodes \nXE.py list3cc"
        
elif MODE == 1:
    print "Running in X-Chat"    
    # Set up all the commands
    xchat.hook_command("XE", hook_xe) 
elif MODE == 2:
    print "Running XE.com Convertion for XBMC"
    vkb = xbmc.Keyboard("1","Enter Amount")
    vkb.doModal()
    Amout = vkb.getText()
    # FOR NOW USE 2 Keyboards
    vkb = xbmc.Keyboard("1","FROM which Country: Enter 3 Digit Country Code ")
    vkb.doModal()
    From = vkb.getText()
    vkb = xbmc.Keyboard("1","TO which Country")
    vkb.doModal()
    To = vkb.getText()
    xbmcgui.Dialog().ok('XE.COM Converter', doConverstion(Amout,From,To) )
    
    



