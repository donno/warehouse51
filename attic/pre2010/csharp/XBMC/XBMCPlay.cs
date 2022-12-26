/*
 * XBMCLaunch 
 *  Using XBMCEvent.cs by Eq2k
 *  By Donno for use as a 'Open with' so it will play the specified
 *  arugment.
 *  
 *  TODO: Ensure XBMC is running if not :) run it and then play
 * 
*/
using System;
using XBMC;

public static class Program {
	[STAThread]
	public static void Main(string[] args) {
		EventClient eventClient = new EventClient();
		eventClient.Connect("127.0.0.1", 9777);
        eventClient.SendHelo("XBMCLaunch");
        if (args.Length == 1) {
            eventClient.SendAction("XBMC.PlayMedia(" + args[0] + ")");
        }            
		eventClient.SendPing();
		eventClient.SendBye();
	}
}
