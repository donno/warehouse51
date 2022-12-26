DRIVE = "I:"

GB = 0
MB = 50

# DO NOT EDIT BELOW HERE
#SIZE = GB * 1024 * 1024 * 1024 + MB * 1024 * 1024

SIZE = 10 * 1024 * 1024 # 10 mb 
numbers = 1024*4
#loops =  SIZE / (numbers * 4)
loops =  SIZE / numbers

kbstring = ""
for n in xrange(0, numbers/4/4):
    kbstring += "%04i" % n

frkbstring = kbstring + kbstring + kbstring + kbstring  # this makes it 4kb

import time
# Writes the file
# returns: time taken
def writer(i):
    print "writing: %s\\temp%02i.tmp" % (DRIVE, i)
    fs = open("%s\\temp%02i.tmp" % (DRIVE, i), 'w')
    startTimeWrite = time.time()
    for n in xrange(0, loops):
        fs.write(frkbstring)
    fs.close()
    endTimeWrite = time.time()
    return endTimeWrite - startTimeWrite

#fourKBNullStr = ""
#for n in xrange(0, 1024):
#    fourKBNullStr += "\0\0\0\0"
b = len(kbstring)
def vertiySub(red):
    #kbstring
    
    #for n in xrange(0, numbers):
    #    print n
    red[4:4]
    
def vertify2(i):
    print "vertify: %s\\temp%02i.tmp" % (DRIVE, i)
    fs = open("%s\\temp%02i.tmp" % (DRIVE, i), 'r')
    for x in xrange(0, loops):
        for n in xrange(0, 4):
            red = fs.read(b) #// 1kb
            if (red != kbstring): 
                #vertiySub(red)
                print "FAILED: loop: %i/%i on %s != '%s" % (x, loops, kbstring , red)
                
    fs.close()

def vertify(i):
    print "vertify: %s\\temp%02i.tmp" % (DRIVE, i)
    fs = open("%s\\temp%02i.tmp" % (DRIVE, i), 'r')
    for x in xrange(0, 1):
        for n in xrange(0, numbers):
            red = fs.read(4)
            if (red != ("%04i" % n)): 
                print "FAILED: loop: %i/%i on %04i != '%s" % (x, loops, n , red)
                
    fs.close()

print writer(2)
print vertify(2)
