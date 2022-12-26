NUMBER = "439180964"


numbers = {
    0 : (' '),
    1 : (' '),
    2 : ('a','b','c'),
    3 : ('d','e','f'),
    4 : ('g','h','i'),
    5 : ('j','k','l'),
    6 : ('m','n','o'),
    7 : ('p', 'q','r','s'),
    8 : ('t','u','v'),
    9 : ('w','x','y','z'),
}

for c in NUMBER:
    i = int(c)
    #if (i > 1):
    print numbers[i]
