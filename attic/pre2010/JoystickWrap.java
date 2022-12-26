/*

javac -classpath .;joystick.jar JoystickWrap.java
java -Djava.library.path=lib -classpath .;Joystick.jar JoystickWrap
*/
import com.centralnexus.input.*;

public class JoystickWrap implements JoystickListener {
	// Z axis = sholuder
	boolean shoulderState = false;

	public void joystickAxisChanged(Joystick j) {
		// fix me
		
		if (j.getZ() < -1.5259021E-5 && j.getZ() > -1.5259023E-5) {
			if ( shoulderState ) {
				System.out.println("Shoulder released");
			}
			shoulderState = false;
		} else if ( j.getZ() > 0.0 )  {
			System.out.println("Accelerate: " + j.getZ());
			shoulderState = true;
		} else {
			System.out.println("Decelerate: " + j.getZ());
			shoulderState = true;
		}
	}

	public void joystickButtonChanged(Joystick j) {		
		int buttons = j.getButtons();
		if (buttons == 0) {
			System.out.println("released");
		} else if ( (buttons & Joystick.BUTTON5) != 0  ) {
			System.out.println("Button 5 pressed");
		} else if ( (buttons & Joystick.BUTTON6) != 0  ) {
			System.out.println("Button 6 pressed");
		} else {
			//System.out.println(Integer.toHexString(j.getButtons()));
		}
		
	}

	public static void main(String[] args) throws java.io.IOException {
		for (int id = -1; id <= Joystick.getNumDevices(); id++) {
			System.out.println("Joystick " + id + ": " + Joystick.isPluggedIn(id));
		}
		
		JoystickListener jl;
		Joystick joy;
		if (args.length == 2) {
			int joystickId = Integer.valueOf(args[1]).intValue();
			joy = Joystick.createInstance(joystickId);
		} else {
			joy = Joystick.createInstance(); // Start using first joystick
		}
		jl = new JoystickWrap();
		joy.addJoystickListener(jl);
		
//		joy.removeJoystickListener(jl);
	}
}
