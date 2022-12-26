
using System.Net;
using System.Net.Sockets;

public class TFTPServer
{

  public TFTPServer()
  {
    int port = 9402;
    IPHostEntry host;

    host = Dns.GetHostEntry("localhost");

    System.Console.WriteLine("GetHostEntry({0}) returns:", "localhost");
    foreach (IPAddress ip in host.AddressList)
    {
      System.Console.WriteLine("    {0}", ip);
    }
    
    Socket listenSocket = new Socket(AddressFamily.InterNetwork, 
                                 SocketType.Stream,
                                 ProtocolType.Tcp);
    IPAddress hostIP = IPAddress.Parse("127.0.0.1");
    //(Dns.GetHostEntry(IPAddress.Any.ToString())).AddressList[1];
    System.Console.WriteLine(hostIP);
    IPEndPoint ep = new IPEndPoint(hostIP, port);
    listenSocket.Bind(ep);
    
    // start listening
    listenSocket.Listen(1);
   
    System.Console.WriteLine("Waiting for a connection...");
    Socket handler = listenSocket.Accept();
    string data = null;

    System.Console.WriteLine("HEY");
    while (true) {
        byte[] bytes = new byte[1024];
        int bytesRec = handler.Receive(bytes);
        data += System.Text.Encoding.ASCII.GetString(bytes,0,bytesRec);
    
        //System.Console.WriteLine( "Text received : {0}", data);      
        if (data.IndexOf("<EOF>") > -1) {
            break;
        }
    }

    System.Console.WriteLine( "Text received : {0}", data);

    byte[] msg = System.Text.Encoding.ASCII.GetBytes(data);
    handler.Send(msg);
    handler.Shutdown(SocketShutdown.Both);
    handler.Close();
    
  }
  
  public static void Main(string[] args)
  {
    TFTPServer server = new TFTPServer();
    System.Console.WriteLine("Starting TFTP Server");
    //while(true);
  }
}
