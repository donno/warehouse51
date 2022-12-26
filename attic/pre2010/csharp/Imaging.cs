using System.Windows.Forms;
using System.Drawing;


namespace Imaging
{
  class Processing
  {
    
    public static Image Resize(Image image, int width)
    {
      double factor = width / (double)image.Size.Width;
      int height = (int)(image.Size.Height * factor);

      System.Console.WriteLine("Resizing image from {0} by {1} to {2} by {3}",
                              image.Size.Width, image.Size.Height,
                              width, height);

      System.Drawing.Bitmap resizedImage =
        new System.Drawing.Bitmap( width, height);
      System.Drawing.Graphics g =
        System.Drawing.Graphics.FromImage(resizedImage);
      g.DrawImage(image.image,
                  new Rectangle(0,0, resizedImage.Width,resizedImage.Height),
                  0,0, image.Size.Width, image.Size.Height,GraphicsUnit.Pixel);
      g.Dispose();
      return new Image(resizedImage);
    }
    
    
    public static Image ResizeAndGreyscale(Image image, int width)
    {
      double factor = width / (double)image.Size.Width;
      int height = (int)(image.Size.Height * factor);

      System.Console.WriteLine("Resizing image from {0} by {1} to {2} by {3}",
                              image.Size.Width, image.Size.Height,
                              width, height);
      System.Console.WriteLine("To grey scale");

      System.Drawing.Imaging.ColorMatrix colourMatrix =
        new System.Drawing.Imaging.ColorMatrix(new float[][]{
        new float[]{0.3f,0.3f,0.3f,0,0},
        new float[]{0.59f,0.59f,0.59f,0,0},
        new float[]{0.11f,0.11f,0.11f,0,0},
        new float[]{0,0,0,1,0,0},
        new float[]{0,0,0,0,1,0},
        new float[]{0,0,0,0,0,1}});


      System.Drawing.Bitmap resizedImage =
        new System.Drawing.Bitmap( width, height);
      System.Drawing.Graphics g =
        System.Drawing.Graphics.FromImage(resizedImage);

      System.Drawing.Imaging.ImageAttributes ia =
        new System.Drawing.Imaging.ImageAttributes();
      ia.SetColorMatrix(colourMatrix);
      g.DrawImage(image.image,
                  new Rectangle(0,0, resizedImage.Width,resizedImage.Height),
                  0,0, image.Size.Width, image.Size.Height,GraphicsUnit.Pixel,
                  ia);
      g.Dispose();
      return new Image(resizedImage);
    }
    
    /*public static Image ToGreyscale(Image image)
    {
      ColorMatrix colourMatrix = new ColorMatrix(new float[][]{
        new float[]{0.3f,0.3f,0.3f,0,0},
        new float[]{0.59f,0.59f,0.59f,0,0},
        new float[]{0.11f,0.11f,0.11f,0,0},
        new float[]{0,0,0,1,0,0},
        new float[]{0,0,0,0,1,0},
        new float[]{0,0,0,0,0,1}});

      Graphics g = Graphics.FromImage(image.image);
      ImageAttributes ia = new ImageAttributes();
      ia.SetColorMatrix(colourMatrix);
      g.DrawImage(img,new Rectangle(0,0,img.Width,img.Height),0,0,img.Width,img.Height,GraphicsUnit.Pixel,ia);
      g.Dispose();
      return image;
    }*/
  }

  class Image
  {
    public System.Drawing.Image image;

    public Image(System.Drawing.Image image)
    {
      this.image = image;
    }
    

    public Image(string filename)
    {
      this.image = System.Drawing.Image.FromFile(filename);
    }

    public Size Size { get { return image.Size; }     }
    
    static void Main(string[] args)
    {
      Image image = new Image("WP_000276.jpg");
      image = Processing.ResizeAndGreyscale(image, 640);
      
      System.Windows.Forms.Form form = new System.Windows.Forms.Form();
      System.Windows.Forms.PictureBox pb = new System.Windows.Forms.PictureBox();
      pb.Image = image.image;
      pb.Dock = DockStyle.Fill;
      form.Controls.Add(pb);
      form.Show();
      Application.Run(form);
    }
  }
  
}