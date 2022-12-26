/*
 *  SetFileTimes 0.1 by Sean Donnellan 2008
 *
 *  Changes the created, modified and creation times of all files in a given folder to 2008-01-01 00:00:00
 *      With each file adding 1 minute to the new date.
 */

class Program  {
	private static string programName = "SetFileTimes";
	private static string programVer  = "0.1";
	private static string programAuthor = "Sean Donnellan";
	private static string programYear = "2008";
	private static string filterExt = "*.avi";
	/*
		Slighly more 'generic'
	public static void SetFileTimes(string path, string filterExt) {
		System.DateTime fileDT = new System.DateTime(2007, 1, 1, 0,0, 0);
		//DateTime(Int32, Int32, Int32, Int32, Int32, Int32) 	Initializes a new instance of the DateTime structure to the specified year, month, day, hour, minute, and second.
		System.Console.WriteLine("Processing: " + path);
		string[] files = System.IO.Directory.GetFiles(path);
		foreach (string file in files) {
			string fileName = System.IO.Path.GetFileName(file);
			string fileExt = System.IO.Path.GetExtension(file);
			if (fileExt == filterExt || filterExt == "") {
				System.IO.FileInfo fi = new System.IO.FileInfo(file);
				System.Console.WriteLine("Processing: " + fi.Name);
				//System.Console.WriteLine("C: " + fi.CreationTimeUtc.ToString("s")
				//+ ". M: " + fi.LastWriteTimeUtc.ToString("s")
				//+ ". A: " + fi.LastAccessTimeUtc.ToString("s")
				//);

				//The next 3 lines are the real work
				fi.LastWriteTimeUtc = fileDT;
				fi.LastAccessTimeUtc = fileDT;
				fi.CreationTimeUtc = fileDT;

				fileDT = fileDT.AddMinutes(1);
			}
		}
		System.Console.WriteLine("Processed: " + path);
	}*/

	public static void SetFileTimes(string path, string filterExt) {
		System.DateTime fileDT = new System.DateTime(2007, 7, 7, 6, 0, 0);
		System.Console.WriteLine("Processing: " + path);
		System.IO.FileInfo[] files = (new System.IO.DirectoryInfo(path)).GetFiles(filterExt);
		foreach (System.IO.FileInfo fi in files) {
			System.Console.WriteLine("Processing: " + fi.Name);
			fi.LastWriteTimeUtc = fi.LastAccessTimeUtc = fi.CreationTimeUtc = fileDT;
			fi.LastWriteTime = fi.LastAccessTime = fi.CreationTime = fileDT;
			fileDT = fileDT.AddMinutes(1);
		}
		System.Console.WriteLine("Processed: " + path);
	}

	static void Main(string[] args) {
		System.Console.WriteLine(programName + " " + programVer + " by " + programAuthor + " (" + programYear + ")");
		if (args.Length == 1) {
			SetFileTimes(args[0], filterExt);
			System.Console.WriteLine("\nThanks for using this tool");
		} else if (args.Length == 2) {
			SetFileTimes(args[0], args[1]);
			System.Console.WriteLine("\nThanks for using this tool");
		} else {
			System.Console.WriteLine("Usage: setfiletimes.exe path [extention]");
			System.Console.WriteLine("Example: setfiletimes.exe D:\\Videos\\IT Crowd\\ *.avi");
		}
	}
}
