/*
 *  MD5File 0.1 by Sean Donnellan (2008)
 *
 *  Calculates the md5sum of all the files in the current directory
 *
 *  Reference: http://support.microsoft.com/kb/889768
 */

class Program {
    private static string programName = "MD5File";
    private static string programVer  = "0.1";
    private static string programAuthor = "Sean Donnellan";
    private static string programYear = "2008";

    private static string filterExt = ".avi";
    
    private static System.Security.Cryptography.MD5CryptoServiceProvider md5 = new System.Security.Cryptography.MD5CryptoServiceProvider();
        
    static void MD5Calc(string fn) {
        System.IO.FileStream fs = new System.IO.FileStream(fn, System.IO.FileMode.Open, System.IO.FileAccess.Read, System.IO.FileShare.Read, 8192);
        md5.ComputeHash(fs);
        System.Text.StringBuilder buff = new System.Text.StringBuilder();
        foreach (byte hashByte in md5.Hash)
        {
            buff.Append(string.Format("{0:X1}", hashByte));
        }
        System.Console.WriteLine("Hash:" + buff.ToString() + "\n");
    }
    public static void ProcessFolder(string path, string filterExt) {
        System.Console.WriteLine("Processing: " + path);
        string[] files = System.IO.Directory.GetFiles(path);
        foreach (string file in files) {
            string fileName = System.IO.Path.GetFileName(file);
            string fileExt = System.IO.Path.GetExtension(file);
            if (fileExt == filterExt || filterExt == "") {
                System.Console.WriteLine("Processing: " + fileName);
                MD5Calc(file);
            }
        }
        System.Console.WriteLine("Processed: " + path);
    }
    
    static void Main(string[] args) {
        System.Console.WriteLine(programName + " " + programVer + " by " + programAuthor + " (" + programYear + ")");
        if (args.Length == 1) {
            ProcessFolder(args[0], filterExt);
            System.Console.WriteLine("\nThanks for using this tool");
        } else if (args.Length == 2) {
            ProcessFolder(args[0], args[1]);
            System.Console.WriteLine("\nThanks for using this tool");
        } else {
            System.Console.WriteLine("Usage: MD5Files.exe path [extention]");
            System.Console.WriteLine("Example: MD5Files.exe D:\\Videos\\IT Crowd\\ *.avi");
        }
    }
}
