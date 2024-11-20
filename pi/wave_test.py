import time
import math
import json
import logging
import yaml

from servo_controller import ServoController  # Your ServoController implementation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Load configuration
def load_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Loaded configuration from {config_file}")
        return config
    except Exception as e:
        logging.error(f"Failed to load configuration file {config_file}: {e}")
        exit(1)

def set_all_angles_to_center(servo_controller, center_angle=90):
    """
    Sets all servos managed by the ServoController to the specified center angle.

    :param servo_controller: Instance of the ServoController.
    :param center_angle: Angle to set for all servos (default: 90 degrees).
    """
    try:
        # Create a list of servo data to set all angles
        servo_data = []
        for (i2c_id, motor_id), servo_obj in servo_controller.servos.items():
            servo_data.append({'i2c_id': i2c_id, 'motor_id': motor_id, 'angle': center_angle})

        # Use the ServoController to set all servo angles
        servo_controller.set_multiple_servo_angles(servo_data)
        logging.info(f"All servos set to {center_angle}°")
    except Exception as e:
        logging.error(f"Failed to set all servos to {center_angle}°: {e}")

def move_left_down_to_right_up(
    servo_controller,
    amplitude=15,
    center_angle=90,
    duration=5,
    delay=0.05,
    step=1
):
    """
    Smoothly moves all pan and tilt servos in a left-down to right-up motion simultaneously.

    :param servo_controller: Instance of ServoController to control the servos.
    :param amplitude: Amplitude of the motion (in degrees).
    :param center_angle: Center angle for the servos.
    :param duration: Duration of the motion (in seconds).
    :param delay: Delay between updates (in seconds).
    :param step: Incremental step for smooth transitions (smaller is smoother).
    """
    import time

    start_time = time.time()

    # Determine pan and tilt servo indices
    pan_servos = []
    tilt_servos = []
    for (i2c_id, motor_id), servo_obj in servo_controller.servos.items():
        if motor_id % 2 == 0:  # Even motor IDs are pan
            pan_servos.append((i2c_id, motor_id))
        else:  # Odd motor IDs are tilt
            tilt_servos.append((i2c_id, motor_id))

    # Define the target angles for left-down and right-up
    pan_left_angle = center_angle - amplitude
    tilt_down_angle = center_angle + amplitude
    pan_right_angle = center_angle + amplitude
    tilt_up_angle = center_angle - amplitude

    while time.time() - start_time < duration:
        # Smoothly transition to left-down position
        smooth_transition(
            servo_controller,
            pan_servos,
            tilt_servos,
            target_pan_angle=pan_left_angle,
            target_tilt_angle=tilt_down_angle,
            step=step,
            delay=delay
        )

        # Smoothly transition to right-up position
        smooth_transition(
            servo_controller,
            pan_servos,
            tilt_servos,
            target_pan_angle=pan_right_angle,
            target_tilt_angle=tilt_up_angle,
            step=step,
            delay=delay
        )


def smooth_transition(
    servo_controller,
    pan_servos,
    tilt_servos,
    target_pan_angle,
    target_tilt_angle,
    step=1,
    delay=0.05
):
    """
    Smoothly transitions all servos to the target pan and tilt angles.

    :param servo_controller: Instance of ServoController to control the servos.
    :param pan_servos: List of (i2c_id, motor_id) for pan servos.
    :param tilt_servos: List of (i2c_id, motor_id) for tilt servos.
    :param target_pan_angle: Target angle for all pan servos.
    :param target_tilt_angle: Target angle for all tilt servos.
    :param step: Incremental step for smooth transitions.
    :param delay: Delay between updates (in seconds).
    """
    import time

    # Get the current angles of all servos
    current_pan_angles = {
        (i2c_id, motor_id): servo_controller.servos[(i2c_id, motor_id)].angle or 0
        for i2c_id, motor_id in pan_servos
    }
    current_tilt_angles = {
        (i2c_id, motor_id): servo_controller.servos[(i2c_id, motor_id)].angle or 0
        for i2c_id, motor_id in tilt_servos
    }

    # Calculate the number of steps needed for smooth movement
    max_steps = max(
        abs(current_pan_angles[key] - target_pan_angle) // step for key in current_pan_angles
    )
    max_steps = max(
        max_steps,
        max(
            abs(current_tilt_angles[key] - target_tilt_angle) // step for key in current_tilt_angles
        ),
    )
    max_steps = int(max_steps) or 1  # Ensure max_steps is at least 1

    # Incrementally move servos to their target angles
    for step_index in range(1, max_steps + 1):
        pan_data = []
        tilt_data = []

        for key, current_angle in current_pan_angles.items():
            new_angle = current_angle + (target_pan_angle - current_angle) * (step_index / max_steps)
            pan_data.append({'i2c_id': key[0], 'motor_id': key[1], 'angle': new_angle})

        for key, current_angle in current_tilt_angles.items():
            new_angle = current_angle + (target_tilt_angle - current_angle) * (step_index / max_steps)
            tilt_data.append({'i2c_id': key[0], 'motor_id': key[1], 'angle': new_angle})

        # Update all angles
        servo_controller.set_multiple_servo_angles(pan_data + tilt_data)

        # Wait before the next update
        time.sleep(delay)



def wave_motion_with_controller(
    servo_controller,
    amplitude=15,
    frequency=1,
    phase_offset=0.1,
    center_angle=90,
    duration=5,
    delay=0.5,
    servo_type='pan'):
    """
    Creates a wave motion selectively for pan or tilt servos using the ServoController.

    :param servo_controller: Instance of ServoController to control servos.
    :param amplitude: Amplitude of the wave (in degrees).
    :param frequency: Frequency of the wave (in Hz).
    :param phase_offset: Phase offset between servos (in radians).
    :param center_angle: Center angle for the servos.
    :param duration: Duration of the wave motion (in seconds).
    :param delay: Delay between updates (in seconds).
    :param servo_type: Type of servos to apply the wave ('pan' or 'tilt').
    """
    import time
    import math

    start_time = time.time()

    # Determine which servos are pan or tilt
    selected_servos = []
    for (i2c_id, motor_id), servo_obj in servo_controller.servos.items():
        if servo_type == 'pan' and motor_id % 2 == 0:  # Even indices are pan
            selected_servos.append((i2c_id, motor_id))
        elif servo_type == 'tilt' and motor_id % 2 == 1:  # Odd indices are tilt
            selected_servos.append((i2c_id, motor_id))

    while time.time() - start_time < duration:
        current_time = time.time()
        servo_data = []

        for index, (i2c_id, motor_id) in enumerate(selected_servos):
            # Calculate the phase for this servo
            phase = phase_offset * index

            # Calculate the angle using the sine wave formula
            angle = center_angle + amplitude * math.sin(2 * math.pi * frequency * current_time + phase)

            # Clamp the angle to the valid range
            angle = max(0, min(180, angle))

            # Add servo movement data
            servo_data.append({'i2c_id': i2c_id, 'motor_id': motor_id, 'angle': angle})

        # Update servo angles in batch
        servo_controller.set_multiple_servo_angles(servo_data)

        # Wait before the next update
        time.sleep(delay)

    # Reset selected servos to the center angle
    for i2c_id, motor_id in selected_servos:
        servo_controller.set_servo_angle(i2c_id, motor_id, center_angle)


def main():
    # Step 1: Load configuration file
    config_path = 'config.yaml'  # Path to your configuration file
    logging.info("Loading configuration...")
    config = load_config(config_path)
    logging.info(f"Configuration loaded: {config}")

    # Step 2: Initialize the servo controller
    logging.info("Initializing servo controller...")
    servo_controller = ServoController(config['pan_tilt_units'])
    logging.info("Servo controller initialized.")

    # Step 3: Simulate wave motion
    try:
        '''
        set_all_angles_to_center(servo_controller, center_angle=90)
        logging.info("Simulating wave motion on pan servos...")
        wave_motion_with_controller(
            servo_controller=servo_controller,
            amplitude=15,            # Amplitude of the wave
            frequency=0.4,           # Frequency of the wave in Hz
            phase_offset=math.pi/4,  # Phase offset between servos
            center_angle=90,         # Center angle for the wave
            duration=10,             # Duration of the wave motion in seconds
            delay=0.05,              # Delay between updates in seconds
            servo_type='pan'         # Apply wave motion to 'pan' servos
        )
        set_all_angles_to_center(servo_controller, center_angle=90)
        logging.info("Simulating wave motion on tilt servos...")
        wave_motion_with_controller(
            servo_controller=servo_controller,
            amplitude=15,            # Amplitude of the wave
            frequency=0.4,           # Frequency of the wave in Hz
            phase_offset=math.pi/4,  # Phase offset between servos
            center_angle=90,         # Center angle for the wave
            duration=10,             # Duration of the wave motion in seconds
            delay=0.05,              # Delay between updates in seconds
            servo_type='tilt'        # Apply wave motion to 'tilt' servos
        )
        '''
        set_all_angles_to_center(servo_controller, center_angle=90)

        logging.info("Starting left-down to right-up motion...")
        move_left_down_to_right_up(
            servo_controller=servo_controller,
            amplitude=15,
            center_angle=90,
            duration=10,
            delay=0.05,
            step=1  # Smaller step for smoother motion
        )
    except KeyboardInterrupt:
        logging.info("Wave motion simulation interrupted by user.")

    # Step 4: Shutdown the servo controller
    finally:
        logging.info("Shutting down servo controller...")
        servo_controller.shutdown()
        logging.info("Servo controller shut down safely.")

if __name__ == "__main__":
    main()
