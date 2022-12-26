# Created April 2009.
import urllib,re, urllib2,os
ul = 'http://www.cdcovers.cc/dvd_'

def getletterLIST(l):
    print "reading Letter list: " + str(l)
    html = urllib.urlopen(ul + str(l) +'.php').read()
    tmp_gid = re.compile('<OPTION value=(.*)>.*').findall(html)
    tmp_title = re.compile('<OPTION value=.*>(.*)').findall(html)
    thelist = ""
    #tf = open("C:\\thelist"+ str(l) +".txt", "a")
    print "Number:" + str(len(tmp_gid))
    for id in range(0,len(tmp_gid)-1):
    #for id in range(0,5):
        print "Movie " +str(id)
        print tmp_title[id]
        txdata  = urllib.urlencode({'titleList':tmp_gid[id], 'part':'front', 'cname':tmp_title[id],'type':'dvd','letter':l,'searchfor':'','submit':"Download+Cover"})
        req = urllib2.Request('http://www.cdcovers.cc/dl.php')
        req.add_header("Referer", "http://www.cdcovers.cc/dl.php")
        req.add_header("Cookie", "__utmb=127001695; __utmz=127001695.1143448914.1.1.utmccn=(referral)|utmcsr=cdcovers.cc|utmcct=/|utmcmd=referral; __utma=127001695.517025715.1143448914.1143448914.1143449865.2; phpAds_geoInfo=au; __utmc=127001695")
        html2 = urllib2.urlopen(req,txdata).read()
        coverstring = re.search('document.the_cover.src="http://covers.cdcovers.cc/show.php[?](.*)"' + "'", html2)
        #thelist =  thelist  + 'http://covers.cdcovers.cc/show.php?' + coverstring.group(1) + "\n"
        os.system('wget "' + 'http://covers.cdcovers.cc/show.php?' + coverstring.group(1) +  '" -O "' +tmp_title[id] + '.jpg"'  )
        #tf.write('http://covers.cdcovers.cc/show.php?' + coverstring.group(1) + "\n")
        #urllib.urlretrieve(coverstring,"e:\\" + tmp_title[id]+".jpg")    
    #tf.close()
    thelist = ""
    print "Check C drive for the list"
    print "Done Letter: " + str(l)
    
#getletterLIST(0)
#getletterLIST("a")
#getletterLIST("b")
#getletterLIST("c")
#getletterLIST("d")
#getletterLIST("e")
#getletterLIST("e")
#getletterLIST("f")
"""
getletterLIST("g")
getletterLIST("h")
getletterLIST("i")
getletterLIST("j")
getletterLIST("k")
getletterLIST("l")
getletterLIST("m")
getletterLIST("n")
getletterLIST("o")
getletterLIST("p")
getletterLIST("q")
getletterLIST("r")
getletterLIST("s")
getletterLIST("t")
getletterLIST("u")
getletterLIST("v")
getletterLIST("w")
getletterLIST("x")
getletterLIST("y")"""
getletterLIST("z")
#"""