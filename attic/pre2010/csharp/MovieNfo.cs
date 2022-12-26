// Reads the NFO files that XBMC (now known as Kodi) could read.
using System.Xml;
using System.Xml.Serialization;
[XmlRoot("movie")]
public class MovieNfo {
    [XmlElement()]
    public string title;

    [XmlElement("year")]
    public int year;

    [XmlElement("outline")]
    public string outline;
    
    [XmlElement("plot")]
    public string plot;
    
    [XmlElement("tagline")]
    public string tagline;
    
    [XmlElement("runtime")]
    public string runtime;

    [XmlElement("watched")]
    public bool watched;

    [XmlElement("mpaa")]
    public string mpaa;

    [XmlElement("path")]
    public string path;

    [XmlElement("id")]
    public string id;

    [XmlElement("filenameandpath")]
    public string filenameandpath;

    [XmlElement("genre")]
    public string genre;

    [XmlElement("credits")]
    public string credits;

    [XmlElement("director")]
    public string director;

    [XmlElement("studio")]
    public string studio;

    private static XmlSerializer serializer = new XmlSerializer(typeof(MovieNfo));

    public static void Main() {
        System.Console.WriteLine("Movie NFO Testbed Method");
        MovieNfo mn = Load();
        if (mn == null) {
            System.Console.WriteLine("Failed to read in nfo");
        } else {
            System.Console.WriteLine(mn.title);
            System.Console.WriteLine(mn.plot);
            System.Console.WriteLine(mn.year);
        }
    }
    
    public static MovieNfo Load() {
        MovieNfo mn = null;
        if (System.IO.File.Exists("Shark.Tale.nfo")){
            using (System.IO.TextReader reader = new System.IO.StreamReader("Shark.Tale.nfo")) {
                mn  = serializer.Deserialize(reader) as MovieNfo;
                reader.Close();
            }
        }
        return mn ;
    }


}