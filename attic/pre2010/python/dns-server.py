# Based on http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/491264
# Minimal python dns server, it only replies with a selected ip in an A record
# Specification:  DOMAIN NAMES - IMPLEMENTATION AND SPECIFICATION @ http://www.ietf.org/rfc/rfc1035.txt

# May be useful: https://tor-svn.freehaven.net/svn/libevent-urz/trunk/evdns.c

# USING: http://sourceforge.net/projects/pydns/ for additional power

import socket


"""
CLASS fields appear in resource records.  The following CLASS mnemonics
and values are defined:
"""
class CLASS:
    IN  = 1 # The Internet
    CS  = 2 # The CSNET class (Obsolete - used only for examples in some obsolete RFCs)
    CH  = 3 # the CHAOS class
    HS  = 4 # Hesiod [Dyer 87]

class QTYPE:
    A       = 1  # a host address
    NS      = 2  # an authoritative name server
    MD      = 3  # a mail destination (Obsolete - use MX)
    MF      = 4  # a mail forwarder (Obsolete - use MX)
    CNAME   = 5  # the canonical name for an alias
    SOA     = 6  # marks the start of # a zone of authority
    MB      = 7  # a mailbox domain name (EXPERIMENTAL)
    MG      = 8  # a mail group member (EXPERIMENTAL)
    MR      = 9  # a mail rename domain name (EXPERIMENTAL)
    NULL    = 10 # a null RR (EXPERIMENTAL)
    WKS     = 11 # a well known service description
    PTR     = 12 # a domain name pointer
    HINFO   = 13 # host information
    MINFO   = 14 # mailbox or mail list information
    MX      = 15 # mail exchange
    TXT     = 16 # text strings

class DNSQuery:
    def __init__(self, data):
        self.data   = data
        self.domain = ''
        self.requestReceived()

    def requestReceived(self):
        data = self.data
        tipo = (ord(data[2]) >> 3) & 15   # Opcode bits
        if tipo == 0:                     # Standard query
          ini = 12
          lon = ord( data[ini] )
          while lon != 0:
            self.domain += data[ini+1:ini+lon+1]+'.'
            ini += lon+1
            lon=ord(data[ini])

    def request(self, ip):
        packet=''
        if self.domain:
            packet += self.data[:2] + "\x81\x80"
            packet += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'   # Questions and Answers Counts
            packet += self.data[12:]                                         # Original Domain Name Question
            packet += '\xc0\x0c'                                             # Pointer to domain name
            packet += '\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'             # Response type, ttl and resource data length -> 4 bytes
            packet += str.join('',map(lambda x: chr(int(x)), ip.split('.'))) # 4bytes of IP
        return packet
    
    def respond(self, socket, addr):
        ip = "10.0.0.1"
        request = self.request(ip)
        socket.sendto(request, addr)
        print 'Request: %s -> Response: %s' % (self.domain, ip)
    
class DNSSever:
    def __init__(self):
        self.udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udps.bind(('',53))
        self.lookupTable = {}
        
    def readLookUpTable(self):
        pass

    def lookupIP(self, domain):
        print "lookupIP(): %s" % domain

    def run(self):
        try:
            while 1:
              data, addr = self.udps.recvfrom(1024)
              p = DNSQuery(data)
              self.lookupIP(p.domain)
              p.respond(self.udps, addr )
        except KeyboardInterrupt:
            print 'Finalize'
        self.udps.close()

class DNSClient:
    def __init__(self):
        # connect port 53
        #self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self.sock.connect
        pass
    
    def lookupHostNameFromIP(self, hostname):
        # Need qtype,  qclass and the address
        qclass  = CLASS.IN
        qtype   = QTYPE.A

    """
        def lookupHostNameFromIP(self, ip):
            import DNS
            DNS.DiscoverNameServers()
            return DNS.revlookup(ip)
    """
def handleCreateDatabase( ):
    # using pyDNS
    
    #r = DNS.DnsRequest( qtype = 'ANY' )
    #res = r.req("google.com",qtype='ANY')
    #res = r.req("google.com",qtype='ANY')
    print res
if __name__ == '__main__':
    print 'dns-server-0.1'
    dnsClient = DNSClient()
    print dnsClient.lookupHostNameFromIP("222.35.72.168")
    print "Done"
    handleCreateDatabase()
    
    dnsServer = DNSSever()
    dnsServer.run();
