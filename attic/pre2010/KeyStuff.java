
import javax.swing.JFrame;
import javax.swing.JPanel;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

import javax.sound.midi.*;

class Midi {
    private static Receiver receiver;

    public static void Setup() throws MidiUnavailableException {
        receiver     = null;
        receiver = MidiSystem.getReceiver();
    }

    public static void Cleanup() {
        if (receiver != null) {
            receiver.close();
            receiver = null;
        }
    }

    public static void SendMessage(int imessage[]) {
        try {
            ShortMessage message = new ShortMessage();
            message.setMessage(imessage[0], imessage[1],imessage[2], imessage[3]);
            if (message != null && receiver != null ) {
                receiver.send(message,  -1);
            }
        } catch (InvalidMidiDataException  imde){
            //throw new DsimComponentException("InvalidMidiDataException");
        }
    }

    public static void SendMessage(int command, int channel, int data1, int data2, long dur) throws InvalidMidiDataException {
        ShortMessage message = new ShortMessage();
        message.setMessage(command, channel,data1, data2);
        if (message != null && receiver != null ) {
            receiver.send(message,  dur);
        }
    }
}


public class KeyStuff extends JPanel implements KeyListener {
    public KeyStuff() {
    }

    public int MidiKey(KeyEvent evt) {
        int keyCode = evt.getKeyCode();
        switch (keyCode) {
            case KeyEvent.VK_F1:
                return 60;
            case KeyEvent.VK_F2:
                return 64;
            case KeyEvent.VK_F3:
                return 68;
            case KeyEvent.VK_F4:
                return 68;
            case KeyEvent.VK_F5:
                return 72;
            default:
                return 0;
        }
    }

    public void keyPressed(KeyEvent evt) {
        // turn note on ( 144)
        int note = MidiKey(evt);
        if (note == 0) return;
        PlayNote( 60 );

    }

    public static void PlayNote( int note ) {
        try {
            Midi.SendMessage(144, 0, note, 90, -1);
            Thread.sleep(500);
            Midi.SendMessage(128, 0, note, 90, -1);
        } catch (java.lang.InterruptedException e) {
        } catch (javax.sound.midi.InvalidMidiDataException e) {}
    }

    public void keyReleased(KeyEvent evt) {
        // turn note off ( 128)
        int note = MidiKey(evt);
        if (note == 0) return;
        try {
            System.out.println(note + " off");
            Midi.SendMessage(128, 0, note, 0, -1);

        } catch (javax.sound.midi.InvalidMidiDataException e) {
        }
    }

    public void keyTyped(KeyEvent evt) {

    }

    public static void main(String args[]) {
        try {
            Midi.Setup();
        } catch (javax.sound.midi.MidiUnavailableException mue) {
            //throw new javax.sound.midi.InvalidMidiDataException ();
            System.out.println(mue.getMessage());
            return;
        }

        JFrame frame = new JFrame();
        frame.setTitle("KeyStuff");
        frame.setSize(300, 200);
        frame.addWindowListener(new WindowAdapter() {
            public void windowClosing(WindowEvent e) {
                Midi.Cleanup();
                System.exit(0);
            }
        });


        java.awt.Container cp  = frame.getContentPane();
        KeyStuff ks = new KeyStuff();
        cp.add(ks);
        frame.setVisible(true);
        frame.addKeyListener(ks);

        PlayNote(60);
        PlayNote(60);
        PlayNote(60);

        Midi.Cleanup();
    }
}