import threading

import tkSimpleDialog
from Tkinter import *
"""
Protocol:

Commands handled by Server:
SOT %name%- Start of Transmission - Recieved when a new client joins
EOT - End of Tramsission - Recevied when a new client leaves

DIF %level% - Difficulty level the client wll paly on [0 = Expert, Hard, Medium, Easy]
RDY %notes% - Tells the server the client is ready to play/start the song and the number of notes

EOS - Tells Server a client is finshed a song.

Commands handled by Client:
PLY %songname% - Play SongName - Server tells the client which song to play
SRT - Start the Song - Once all otehr players are ready.
OKY - Connection worked (aka not already in a song)

-- Example ---
[Client] Sends SOT Donno
[Server] Sends either OKY or ING in respond
--- Client waits for Server to pic ksong
[Server] Sends PLY songs/Packs/Guitar Hero II\sweetchild
---- Clients pick difficutly
[Client] Sends DIF 3
[Client] Sends RDY 1251

[Server] Sends SRT

GAME in progress new clients are rejected with a ING
[Client] Sends END

[Server] Sends RES followed by results +
-------------------------------------------
Server chooses a Song (PLY SONGNAME)
Client chooses Difficulty and tells Server


"""
from socket import *
buf = 1024

dataPath = "I:/FretsOnFireX/data"
dataPath = "C:\\Users\\Public\\Games\\FretsOnFireX\data\\"
pack = "Guitar Hero II"


__TIITLE__ = "FoFiX - LAN"

difficulties = ["Expert", "Hard", "Medium", "Easy"]

import os


HAS_FOFIX = True
try:
    from Resource import Resource
except ImportError:
    HAS_FOFIX = False


class FakeEngine:
    def __init__ ( self ):
        import Config
        self.config    = Config.load("foflan.ini",True)
        self.config.set("game", "songlist_instrument", 0)
        self.resource  = Resource( dataPath )

class ClientInfo:
    def __init__(self , name, addr ):
        self.name = name
        self.addr = addr
        self.ready = False
        self.difficulty = -1
        self.instrument = -1
        self.totalNotes = 0
        self.notes = 0

class SongChooser:
    def __init__( self ):
        self.choice = None

    def display( self ):
        import Song
        # Get Song List
        library = "songs/Packs/" + pack
        self.playing = False
        engine = FakeEngine ()

        self.songs = Song.getAvailableSongs( engine, library )
        del engine

        # Show Song List
        self.root = Tk()
        self.root.title(__TIITLE__  + " - Song Selection")
        s = Scrollbar()
        w = Listbox ( self.root, width = 80, height= 40 )
        self.lstBox = w
        w.bind("<Double-1>", self.choose)
        s.pack(side=RIGHT, fill=Y)
        w.pack(side=LEFT, fill=Y)
        s.config(command=w.yview)
        w.config(yscrollcommand=s.set)
        for song in self.songs:
            w.insert( END ,  "%s by %s" % ( song.getName() , song.getArtist() ) )
        self.root.mainloop()

    def choose( self , event):
        self.choice = self.songs[int(self.lstBox.curselection()[0])]
        self.root.destroy()

class DiffChoser:
    def __init__( self ):
        self.choice = None
        
    def display( self ):
        self.root = Tk()
        self.root.title(__TIITLE__  + " - Difficulty Selection")
        s = Scrollbar()
        w = Listbox ( self.root, width = 80, height= 40 )
        self.lstBox = w
        w.bind("<Double-1>", self.choose)
        s.pack(side=RIGHT, fill=Y)
        w.pack(side=LEFT, fill=Y)
        s.config(command=w.yview)
        w.config(yscrollcommand=s.set)
        for diff in difficulties:
            w.insert( START ,  diff )
        self.root.mainloop()

    def choose( self , event):
        self.choice = self.lstBox.curselection()[0]
        self.root.destroy()

class Server(threading.Thread):
    def __init__( self , host = "localhost" , port = 16556):
        self.host = host
        self.port = port
        self.sock = socket( AF_INET, SOCK_DGRAM)
        self.sock.bind( (host,port) )
        self.clients = []
        self.state = 0 # 0 = waiting for players, 1 = waiting for players to be ready
        self.running = True
        threading.Thread.__init__( self )
        print "Started Server"

    def run( self ):
        while self.running:
            data,addr = self.sock.recvfrom(buf)
            if not data:
                print "[Server] ERROR: Invalid Data"
            else:
                if ( len(data) > 3 ):
                    if ( data[:3] == "SOT"):
                        name = data[3:]
                        self.onClientEnter(addr, name)
                    else:
                        print "MSG: ", data , addr
                elif ( data == "EOT" ):
                    self.onClientLeave(addr)
                else:
                    print "MSG: ", data , addr


    def chooseSong( self ):
        #sC = SongChooser()
        #sC.display()
        #result = sC.choice
        #self.song = result.fileName.replace(dataPath, "")[:-9]
        #self.songInfo = result.getName() + " - " + result.getArtist()
        
        # SLEEP HERE
        import time
        time.sleep(5)
        self.songInfo = "Sweet Child O' Mine - Guns N' Roses"
        self.song = "songs/Packs/Guitar Hero II\sweetchild"
        self.send("PLY %s" % self.song)
        # MSG:  PLY songs/Packs/Guitar Hero II\sweetchild ('127.0.0.1', 16556)
        print self.songInfo

    def close( self ):
        self.sock.close()

    def send(self , data ):
        for client in self.clients:
            self.sock.sendto(data, client.addr )

    def onClientEnter ( self , addr , name):
        print "[Server] New Client: %s:%s " % addr
        if self.state > 0:
            self.clients.append( ClientInfo( name, addr) )
            self.sock.sendto("OKY", addr)
            print "=== Player Count %d ===" % len(self.clients)
        else:
            self.sock.sendto("ING", addr)

    def onClientLeave ( self , addr ):
        print "[Server] Client Left: %s:%s " % addr
        c = None
        for client in self.clients:
            if (client.addr == addr):
                c = client
        if (c is not None):
            self.clients.remove(c)

class Client(threading.Thread):
    def __init__( self , host = "localhost" , port = 16556):
        self.status = 0
        self.host = host
        self.port = port
        #self.root = Tk()
        self.nickname = "Donno" # tkSimpleDialog.askstring("FoFiX - LAN", "Nickname",parent=self.root)
        self.sock = socket( AF_INET, SOCK_DGRAM)
        self.msg_buffer = []
        self.running = True
        threading.Thread.__init__( self )
        self.send("SOT %s" % self.nickname )
        self.status = 1 # waiting for reply
        print "Client Started"
        self.song = ""

    def send(self , data ):
        self.sock.sendto(data, (self.host, self.port) )

    def stop( self ):
        self.running = False
        self.send("EOT")
        self.sock.close()
    # Keep Connection Alive
    def run ( self ):
        while self.running:
            data,addr = self.sock.recvfrom(buf)
            if data:
                if self.status == 1:
                    if data == "OKY":
                        self.status = 2
                        print "> Now Waiting for the Song to play"
                    elif data == "ING":
                        print "Game In Progress Disconnecting"
                        self.running = False
                        self.sock.close()
                elif self.status == 2:
                    print data
                    if data[:3] == "PLY" and len(data) > 5:
                        self.song = data[4:] 
                        print "> Song Chosen, now Select Difficulty"
                        self.status = 3
                        # Need to get SongInfo for the given song to display
                        songtitle = os.path.basename(os.path.dirname(self.song))
                        dc = DiffChoser(songtitle)
                        dc.display()
                        dc.choice
                else:
                    print data



def startServer():
    serv = Server()
    serv.start()
    serv.chooseSong()

def startClient():
    client = Client()
    client.start()

    client.send("Hey")

    client.send("Hello")
    #client.stop()

import sys

if (len(sys.argv) == 2):
    if sys.argv[1] == "server":
        startServer()
    else:
        startClient()
else:
    startClient()