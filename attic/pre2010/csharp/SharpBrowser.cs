/* Components
        * Layout Render/Web Engine
        * Browser - eg menus, gui, plugin support
*/
namespace SharpWebKit {
    
    public class XHTMLRender {

    }
    
    public static class General {
        public static void RenderText(System.Drawing.Graphics graphics, string text, float x, float y) {
            System.Drawing.Font drawFont = new System.Drawing.Font("Arial", 16);
            System.Drawing.SolidBrush drawBrush = new System.Drawing.SolidBrush(System.Drawing.Color.Black);
            graphics.DrawString(text, drawFont, drawBrush, x, y);
            drawFont.Dispose();
            drawBrush.Dispose();
            graphics.Dispose();
        }
        
        public static void GetPage(string url) {
            
        }
    }
}

public class SharpBrowser: System.Windows.Forms.Form {
    public SharpBrowser() {
        this.Name = "SharpBrowser";
        this.Text   = "SharpBrowser";
        this.Width = 720;
        this.Height = 576;
        
    }
    protected override void OnPaint ( System.Windows.Forms.PaintEventArgs e ) {
        
        SharpWebKit.General.RenderText(this.CreateGraphics(), "hey", 0F, 5F);
    }
    
    public static void Main() {
            System.Windows.Forms.Application.EnableVisualStyles();
            System.Windows.Forms.Application.SetCompatibleTextRenderingDefault(false);
            System.Windows.Forms.Application.Run(new SharpBrowser());
    }
}