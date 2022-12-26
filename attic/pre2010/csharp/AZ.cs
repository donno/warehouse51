public class Program {
    public static void WriteWC(System.ConsoleColor color, string text) {
        System.ConsoleColor originalColor = System.Console.ForegroundColor;
        System.Console.ForegroundColor = color;
        System.Console.Write(text);
        System.Console.ForegroundColor = originalColor;
    }

    public static void Main() {
        WriteWC(System.ConsoleColor.Green, "Typing A-Z tool by Sean Donno (darkdonno@gmail.com)\nVersion: 0.2\n\n");
        //int lastKey = (int)'a' - 1;
        int lastKey =  64;
        int key = 0;

        while (true) {
            key = System.Console.ReadKey().Key.ToString()[0];
            if (lastKey == (key - 1)) {
                lastKey = key;
                if (key == 90) {
                    WriteWC(System.ConsoleColor.Green, "\n\tCorrect: A-Z in right order.\nStarting Again\n\n");
                    lastKey = 64;
                }
            } else if (key == 85 || key == 82 || 76 == key || key == 68) {
            } else {
                WriteWC(System.ConsoleColor.Red, "\n\tWRONG: TRY AGAIN\n");
                lastKey = 64;
            }
        }
    }
}