public class Version {
    public int major;
    public int minor;
    public char extra;   
    public Version(int major, int minor) {
        this.major = major; this.minor = minor; this.extra = ' ';
    }
    public Version(int major, int minor, char extra) {
        this.major = major; this.minor = minor; this.extra = extra;
    }
    public override string ToString() {
        return this.major + "." + this.minor;
    }
}

public interface ITool {
    string pluginName {
      get;
    }
    Version pluginVersion {
      get;
    }
    string pluginAbout {
      get;
    }
    string pluginDescription {
      get;
    }
    short pluginYear {
      get;
    }

    void ProcessPath(string path);
    void ProcessFile(string file);
    void ProcessStart();
    void ProcessEnd();
/*
    Property InputParameters() As Generic.List(Of InputParameter)
    ReadOnly Property OutputParameters() As Generic.List(Of OutputParameter)
    Sub Initialize(ByVal Host As IHost)
    Sub Start()
    Sub HostClosing(ByRef Cancel As Boolean)
    Sub Close()
    Sub About()
    Sub Settings()
*/
}

public class CTool : ITool {
    protected static string toolName = "";
    protected static Version toolVer = new Version(0,0);
    protected static string toolAbout = "";
    protected static string toolDescr = "";
    protected static short toolYear   = 2008;
        

    public string pluginName        { get { return toolName;    } set{}}
    public Version pluginVersion     { get { return toolVer;      } set{}}
    public string pluginAbout       { get { return toolAbout;   } set{}}
    public string pluginDescription { get { return toolDescr; } set{}}
    public short  pluginYear        { get { return toolYear;    } set{}}

    public virtual void ProcessPath(string path) {}
    public virtual void ProcessFile(string file) {}
    public virtual void ProcessStart() {}
    public virtual void ProcessEnd() {}
}

class SetFileTimes : CTool {
    System.DateTime fileDT = new System.DateTime(2008, 1, 1, 0,0, 0);
    
/*    public ovveride void ProcessPath(string path) {
        System.Console.WriteLine("Processing: " + path);
        System.IO.FileInfo[] files = (new System.IO.DirectoryInfo(path)).GetFiles(filterExt);
        foreach (System.IO.FileInfo fi in files) {
            System.Console.WriteLine("Processing: " + fi.Name);
            fi.LastWriteTimeUtc = fi.LastAccessTimeUtc = fi.CreationTimeUtc = fileDT;
        }
        System.Console.WriteLine("Processed: " + path);
    }*/
    public override void ProcessFile(string file) {
        string fileName = System.IO.Path.GetFileName(file);
        string fileExt  = System.IO.Path.GetExtension(file);
        System.IO.FileInfo fi = new System.IO.FileInfo(file);
        System.Console.WriteLine("Processing: " + fi.Name);
        //System.Console.WriteLine("C: " + fi.CreationTimeUtc.ToString("s")
        //+ ". M: " + fi.LastWriteTimeUtc.ToString("s")
        //+ ". A: " + fi.LastAccessTimeUtc.ToString("s")
        //);

        /* Main Payload/work */
        fi.LastWriteTimeUtc = fi.LastAccessTimeUtc = fi.CreationTimeUtc = fileDT;
        fileDT = fileDT.AddMinutes(1);
    }

}

class Program {

    public static void Main(string[] args) {
        ITool tool = new SetFileTimes();
        
        System.Console.WriteLine(tool.pluginName + " " + tool.pluginVersion + " by " + tool.pluginAbout + " (" + tool.pluginYear + ")");
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