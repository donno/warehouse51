using System;
using System.Linq;
using System.Collections.Generic;

public class Program {
    public static void Main() {
      // First case
      {
        Dictionary<string, string> openWith = 
            new Dictionary<string, string>();

        // Add some elements to the dictionary. There are no  
        // duplicate keys, but some of the values are duplicates.
        openWith.Add("txt", "notepad.exe");
        openWith.Add("bmp", "paint.exe");
        openWith.Add("dib", "paint.exe");
        openWith.Add("rtf", "wordpad.exe");
        
        System.Console.WriteLine(
          openWith.Values.Any(v => v.Equals("notepad.exe")) ? "Has notepad" : "No notepad");
      }

      // Second case: This will print out "There is a bmp" ie any returns false,
      // when the list is empty.
      {
        Dictionary<string, string> openWith = 
            new Dictionary<string, string>();
        
        System.Console.WriteLine(
          openWith.Values.Any(v => v.Equals("notepad.exe")) ? "Has notepad" : "No notepad");
      }
    }
}