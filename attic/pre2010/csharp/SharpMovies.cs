[assembly: System.Reflection.AssemblyTitle("SharpMovieBrowser")]
[assembly: System.Reflection.AssemblyVersion("1.0.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("1.0.0.0")]
namespace SharpMovies {
    [System.Xml.Serialization.XmlRoot("movie")]
    public class MovieNfo {
        public string title;
        public int year;
        public string outline;
        public string plot;
        public string tagline;
        public string runtime;
        public bool watched;
        public string mpaa;
        public string path;
        public string id;
        public string filenameandpath;
        public string genre;
        public string credits;
        public string director;
        public string studio;

        public override string ToString() {
            return System.String.Format("{0}\nOutline: {1}\nPlot: {2}\nTagline: {3}\nRuntime: {4}\nMPAA:{5}\nPath: {6}\nimdbID: {7}\nFilenameandpath: {8}\nGenre: {9}\nCredits: {10}\nDirector: {11}\nStudio: {12}", 
                title, outline, plot, tagline, runtime, mpaa, path, id, filenameandpath, genre, credits, director, studio);
        }

        private static System.Xml.Serialization.XmlSerializer serializer = new System.Xml.Serialization.XmlSerializer(typeof(MovieNfo));
        public static MovieNfo Load(string filename) {
            MovieNfo mn = null;
            if (System.IO.File.Exists(filename)) {
                using (System.IO.TextReader reader = new System.IO.StreamReader(filename)) {
                    mn  = serializer.Deserialize(reader) as MovieNfo;
                    reader.Close();
                }
            }
            return mn ;
        }
    }

    public struct FileItem {
        public string filename;
        public string fullpath;
        public string fileext;
        public MovieNfo filenfo;
        public FileItem(string fullpath, string filename,  string fileext) {
            this.filename = filename;
            this.fullpath  = fullpath;
            this.fileext  = fileext;
            if (System.IO.File.Exists(fullpath.Replace(fileext,".nfo"))) {
                this.filenfo = MovieNfo.Load(fullpath.Replace(fileext,".nfo"));
            } else {
                this.filenfo = null;
            }
            
            
        }
    }
    public class SharpMovieBrowser: System.Windows.Forms.Form {
        public SharpMovieBrowser() {
            this.Name = "SharpMovieBrowser";
            this.Text   = "Sharp Movie Browser";
            this.Width = 720;
            this.Height = 576;
            this.fileList = new System.Collections.Generic.List<FileItem>();
            this.InitializeComponent();
            this.txtPath.Text  = "F:\\Videos\\Movies\\";
            this.GoPath();
        }

        private void InitializeComponent() {
            this.lstMovies = new System.Windows.Forms.ListBox();
            this.lstMovies.Width = 320;
            this.lstMovies.SelectedIndexChanged  += new System.EventHandler(MovieList_SelectChange);
            this.lstMovies.Dock = System.Windows.Forms.DockStyle.Right;

            this.txtPath = new System.Windows.Forms.TextBox();
            this.txtPath.Dock = System.Windows.Forms.DockStyle.Top;
            this.txtBox = new System.Windows.Forms.RichTextBox();
            this.txtBox.Height = 120;
            this.txtBox.Dock = System.Windows.Forms.DockStyle.Bottom;
            this.pbThumbnail = new System.Windows.Forms.PictureBox();
            this.pbThumbnail.Width = 280;
            this.pbThumbnail.Height = 425;
            this.pbThumbnail.Top = 25;
            this.pbThumbnail.SizeMode = System.Windows.Forms.PictureBoxSizeMode.StretchImage;
            this.pbThumbnail.Dock = System.Windows.Forms.DockStyle.None;
            this.BackColor = System.Drawing.Color.FromName("white");
            this.Controls.Add(this.lstMovies);
            this.Controls.Add(this.txtBox);
            this.Controls.Add(this.txtPath);
            this.Controls.Add(this.pbThumbnail);
        }


        public void MovieList_SelectChange(object sender, System.EventArgs e) {
            FileItem fi = this.fileList[this.lstMovies.SelectedIndex];
            if (fi.filenfo != null) {
                this.txtBox.Text = fi.filenfo.ToString();
            }
            this.pbThumbnail.Load(System.IO.Path.ChangeExtension(fi.fullpath, "tbn"));
        }
        
        public static void Main() {
                System.Windows.Forms.Application.EnableVisualStyles();
                System.Windows.Forms.Application.SetCompatibleTextRenderingDefault(false);
                System.Windows.Forms.Application.Run(new SharpMovieBrowser());
        }

        public void GoPath() {
            GoPath(this.txtPath.Text);
        }
        public void RefreshList() {
            this.lstMovies.Items.Clear();
            foreach (FileItem fi in this.fileList) {
                if (fi.filenfo == null) {
                    this.lstMovies.Items.Add(fi.filename);
                } else {
                    this.lstMovies.Items.Add(fi.filenfo.title);
                }
            }
        }

        public void GoPath(string path) {
            //  .m4v|.3gp|.nsv|.ts|.ty|.strm|.pls|.rm|.rmvb|.m3u|.ifo|.mov|.qt|.divx|.xvid|.bivx|.vob|.nrg|.img|.iso|.pva|.wmv|.asf|.asx|.ogm|.m2v|.avi|.bin|.dat|.mpg|.mpeg|.mp4|.mkv|.avc|.vp3|.svq3|.nuv|.viv|.dv|.fli|.flv|.rar|.001|.wpl|.zip|.vdr|.dvr-ms|.xsp
            string[] videoExtention = { ".avi", ".mp4", ".mpg"};
            if (System.IO.Directory.Exists(path)) {
                this.fileList.Clear();
                string[] files = System.IO.Directory.GetFiles(path);
                foreach (string file in files) {
                    string fileExtension = System.IO.Path.GetExtension(file);
                    string fileName = System.IO.Path.GetFileNameWithoutExtension(file);
                    int i = System.Array.IndexOf<string>(videoExtention, fileExtension);
                    if (i > -1) {
                        this.fileList.Add(new FileItem(file, fileName, fileExtension));
                    }
                }
                RefreshList();
            } else {
                Dialog("Path doesn't exist");
            }
        }
        
        public void Dialog(string message) {
            System.Windows.Forms.MessageBox.Show(message);
        }
        
        private System.Collections.Generic.List<FileItem> fileList;
        internal System.Windows.Forms.TextBox txtPath;
        internal System.Windows.Forms.RichTextBox txtBox;
        internal System.Windows.Forms.ListBox lstMovies;
        internal System.Windows.Forms.PictureBox pbThumbnail;
    }
}