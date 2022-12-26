/*
        By Donno.
        Copyright (C) Sean Donnellan 2008   [darkdonno@gmail.com]
            My First C# Game. It has some bugs left in it :)
            - Needs AI and better closing down code.
            - Needs some cleaning/smoothing. maybe make players into a struct with x,y,d  maybe name
*/

struct Player {
    public int n; // Player Number
    public int x; // X Position
    public int y; // Y Position
    public int d; // Direction
    public static int nd = 1;
    public Player(int x, int y) {
        this.x = x;
        this.y = y;
        this.d = 4;
        this.n = nd;
        nd = nd + 1;
    }
}

class Program  {
    private static string programName = "SharpTron";
    private static string programVer  = "0.1";
    private static string programAuthor = "Sean Donno";
    private static string programYear = "2008";

    private static System.Timers.Timer aTimer;
    
    private static Player p1 = new Player(24,24);
    private static Player p2 = new Player(64,24);

    private static bool stillplaying = true;
    private static bool[,] grid = new bool[94,47];
    
    public static void drawPart(int x, int y, int p) {
        System.ConsoleColor org = System.Console.ForegroundColor;
        if (p == 1) {
            System.Console.ForegroundColor = System.ConsoleColor.Red;
        } else if (p == 2) {
            System.Console.ForegroundColor = System.ConsoleColor.Green;
        }
        System.Console.SetCursorPosition(x,y);
        System.Console.Write("@");
        System.Console.ForegroundColor = org;
        
    }
    public static void Main(string[] args) {
        System.Console.Clear();
        System.Console.Title = programName;
        int origRow = System.Console.CursorTop;
        int origCol  = System.Console.CursorLeft;
        System.Console.WriteLine(programName + " " + programVer + " by " + programAuthor + " (" + programYear + ")");
        for (int i = 0; i < 95; i++) {
            System.Console.Write("#");
        }
        System.Console.WriteLine();
        for (int y = 1; y < 46; y++) {
            System.Console.Write("#");
            for (int i = 1; i < 94; i++) {  System.Console.Write(" ");  }
            System.Console.WriteLine("#");
        }
        
        for (int i = 0; i < 95; i++) {
            System.Console.Write("#");
        }
        System.Console.WriteLine();
        p1.d = 0;
        aTimer = new System.Timers.Timer(1000);
        aTimer.Elapsed += new System.Timers.ElapsedEventHandler(OnTimedEvent);
        aTimer.Interval = 100;
        aTimer.Enabled = false;
        drawPart(p1.x,p1.y,1);
        drawPart(p2.x,p2.y,2);
        System.ConsoleKeyInfo cki;
        while ((cki = System.Console.ReadKey()).Key != System.ConsoleKey.Escape && stillplaying) {
            if (cki.Key ==System.ConsoleKey.UpArrow) {
                p1.d = 8;
                aTimer.Enabled = true;
            } else if (cki.Key ==System.ConsoleKey.DownArrow) {
                p1.d = 2;
                aTimer.Enabled = true;
            } else if (cki.Key ==System.ConsoleKey.RightArrow) {
                p1.d = 6;
                aTimer.Enabled = true;
            } else if (cki.Key ==System.ConsoleKey.LeftArrow) {
                p1.d = 4;
                aTimer.Enabled = true;
            }
            
            if (cki.Key ==System.ConsoleKey.W) {
                p2.d = 8;
            } else if (cki.Key ==System.ConsoleKey.S) {
                p2.d = 2;
            } else if (cki.Key ==System.ConsoleKey.D) {
                p2.d = 6;
            } else if (cki.Key ==System.ConsoleKey.A) {
                p2.d = 4;
            }
        }
        System.Console.ResetColor();
    }

    private static void AdjustPosition(Player player) {
        if (player.d == 6) {
            player.x = player.x - 1;
        } else if (player.d == 4) {
            player.x = player.x + 1;
        } else if (player.d == 8) {
            player.y = player.y - 1;
        } else if (player.d == 2) {
            player.y = player.y + 1;
        }
    }
    private static void OnTimedEvent(object source, System.Timers.ElapsedEventArgs e) {
        bool player1Alive =  p1.x > 0 && p1.x < 94 && p1.y > 1 && p1.y < 47;   
        bool player2Alive =  p2.x > 0 && p2.x < 94 && p2.y > 1 && p2.y < 47;
        if (!player1Alive || !player2Alive || p1.d == 0) {
            return;
        }

        AdjustPosition(p1);
        AdjustPosition(p2);
        
        player1Alive =  p1.x > 0 && p1.x < 94 && p1.y > 1 && p1.y < 47;   
        player2Alive =  p2.x > 0 && p2.x < 94 && p2.y > 1 && p2.y < 47;
        
        player1Alive = player1Alive && (grid[p1.x,p1.y] == false);
        player2Alive = player2Alive && (grid[p2.x,p2.y] == false); /* Check grid if its == false then there is no trail there */
        
        if (player1Alive && player2Alive) {
            drawPart(p1.x,p1.y,1);
            drawPart(p2.x,p2.y,2);
            grid[p1.x,p1.y] = true;
            grid[p2.x,p2.y] = true;
        } else if (!player1Alive && !player2Alive) {
            System.Console.SetCursorPosition(0,48);
            System.Console.WriteLine("Draw, both players died");
            stillplaying = false;
            p1.d = 0;
        } else if (player1Alive && !player2Alive) {
            System.Console.SetCursorPosition(0,48);
            System.Console.WriteLine("Player 1 Wins");
            stillplaying = false;
            p1.d = 0;
        } else if (!player1Alive && player2Alive) {
            System.Console.SetCursorPosition(0,48);
            System.Console.WriteLine("Player 2 Wins");
            p1.d = 0;
            stillplaying = false;
        } 
        System.Console.SetCursorPosition(84,0);
    }
}
