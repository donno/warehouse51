"""
Usage:
    imdb2dot.py > imdb.dot
    dot -T png -o imdb.png imdb.dot
"""
outputToTerm = 0

class Dot:
    def __init__(self, name):
        self.header = "digraph %s {" % name
        #self.declare = "\trankdir=LR;\n"
        self.declare =  "\tsize=\"500, 500\"\n"
        self.declare =  "\tnode [shape = circle];"
        self.tail = "}"
        self.middle = ""

    def generate(self, arr):
        for item in arr:
            self.middle += "\t%s -> %s;\n" % (item[0], item[1])

    def writeFile(self, filename):
        fs = open(filename, "w")
        fs.write(self.header + "\n")
        fs.write(self.declare + "\n")
        fs.write(self.middle)
        fs.write(self.tail)
        fs.close()

    def writeFile2(self, filename, ilDB):
        fs = open(filename, "w")
        fs.write(self.header + "\n")
        fs.write(self.declare + "\n")
        fs.write(self.middle)
        for movieID in iLDB.imdbMoviesList:
            title, n, n1 = iLDB.imdbMoviesList[movieID]
            if (title == ""):
                #fs.write("\ttt%s [label=\"%s\"]; \n" % (movieID, title))
                pass
            else:
                title = title.replace("\"", "\\\"");
                fs.write("\ttt%s [label=\"%s\"]; \n" % (movieID, title))
            
        fs.write("\tnode [shape = box];")
        for actorID in iLDB.imdbActorsList:
            name, n, n1 = iLDB.imdbActorsList[actorID]
            fs.write("\tch%s [label=\"%s\"]; \n" % (actorID, name))


        iLDB.c.execute("SELECT imdbLinks.* FROM imdbLinks;")
        for row in iLDB.c:
            fs.write("\ttt%s -> ch%s\n" % (row[1], row[2]))

        fs.write(self.tail)
        fs.close()



    def output(self):
        print self.header
        print self.declare
        print self.middle
        print self.tail

import sqlite3

class imdbLinkerDB:
    def __init__(this):
        this.imdbMoviesList = {}
        this.imdbActorsList = {}
        this.conn = sqlite3.connect("imdbLinker.db")
        this.conn.text_factory = str
        this.c = this.conn.cursor()

        this.LoadMovies()
        print "imdbLinkerDB movies loaded"
        this.LoadActors()
        print "imdbLinkerDB actors loaded"
        print "Stats: %li movies, %li actors" % (len(this.imdbMoviesList), len(this.imdbActorsList))
        this.LoadUnIndex()
        print "imdbLinkerDB unindex loaded"
        this.numberOfMovies = len(this.imdbMoviesList)
        this.numberOfActors = len(this.imdbActorsList)
        # All Setup
        print "imdbLinkerDB init stage completed"
        print "Stats: %li movies, %li actors" % (this.numberOfMovies, this.numberOfActors)

    def LoadMovies(this):
        this.c.execute("SELECT * FROM imdbTitles;")
        for row in this.c:
            this.imdbMoviesList[row[0]] = (row[1], 0, 0)

    def LoadActors(this):
        this.c.execute("SELECT * FROM imdbActors;")
        for row in this.c:
            this.imdbActorsList[row[0]] = (row[1], 0, 0)

    def LoadUnIndex(this):
        # This Gets unkonwn movieids
        this.c.execute("SELECT DISTINCT imdbLinks.movieid FROM imdbLinks WHERE imdbLinks.movieid NOT IN (SELECT imdbTitles.id FROM imdbTitles);")
        for row in this.c:
            this.imdbMoviesList[row[0]] = ("",0,0)
        this.c.execute("SELECT DISTINCT imdbLinks.actorid FROM imdbLinks WHERE imdbLinks.actorid NOT IN (SELECT imdbActors.id FROM imdbActors);")
        # This Gets unkonwn actors
        for row in this.c:
            this.imdbActorsList[row[0]] = ("",0,0)

iLDB = imdbLinkerDB()


d = Dot("titleLinker")

#arr = [["Smallville", "Lilly"], ["Lilly", "Lost"]]

##fs.write('tt [label="Hello, World!"]')
#d.generate(arr)

if outputToTerm:
    d.output()
else:
    print "Writting imdb.dot file"
    d.writeFile2("imdb.dot", iLDB)
    #d.writeFile("imdb.dot")
    from os import system
    print "Generating imdb.png using dot"
    system("dot -T png -o imdb.png imdb.dot")
"""
	
	LR_0 -> LR_2 [ label = "tt1162084" ];
	LR_0 -> LR_1 [ label = "SS(S)" ];
	LR_1 -> LR_3 [ label = "S($end)" ];
	LR_2 -> LR_6 [ label = "SS(b)" ];
	LR_2 -> LR_5 [ label = "SS(a)" ];
	LR_2 -> LR_4 [ label = "S(A)" ];
	LR_5 -> LR_7 [ label = "S(b)" ];
	LR_5 -> LR_5 [ label = "S(a)" ];
	LR_6 -> LR_6 [ label = "S(b)" ];
	LR_6 -> LR_5 [ label = "S(a)" ];
	LR_7 -> LR_8 [ label = "S(b)" ];
	LR_7 -> LR_5 [ label = "S(a)" ];
	LR_8 -> LR_6 [ label = "S(b)" ];
	LR_8 -> LR_5 [ label = "S(a)" ];
}"""