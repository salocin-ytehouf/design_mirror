# servo_controller.py

import time
import logging
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class ServoController:
    def __init__(self, units_config):
        """Initialize the servo controllers based on the units configuration."""
        self.i2c_buses = {}         # Map from i2c_id to I2C bus
        self.pca_controllers = {}   # Map from i2c_id to PCA9685 controller
        self.servos = {}            # Map from (i2c_id, motor_id) to servo object

        # Initialize the I2C buses and PCA9685 controllers
        for unit in units_config:
            i2c_id = unit['i2c_id']
            motors_id = unit['motors_id']

            # Initialize I2C bus and PCA9685 controller if not already initialized
            if i2c_id not in self.pca_controllers:
                self._initialize_pca_controller(i2c_id)

            # Initialize the servos for this unit
            for motor_id in motors_id:
                self._initialize_servo(i2c_id, motor_id)

    def _initialize_pca_controller(self, i2c_id):
        """Initialize a single PCA9685 controller on the given I2C bus."""
        try:
            i2c_bus = busio.I2C(board.SCL, board.SDA)
            i2c_address = 0x40 + i2c_id  # Map i2c_id to I2C address
            pca = PCA9685(i2c_bus, address=i2c_address)
            pca.frequency = 50  # Set frequency for servos
            self.i2c_buses[i2c_id] = i2c_bus
            self.pca_controllers[i2c_id] = pca
            logging.info(f"Initialized PCA9685 controller at address {hex(i2c_address)} for i2c_id {i2c_id}")
        except Exception as e:
            logging.error(f"Failed to initialize PCA9685 for i2c_id {i2c_id}: {e}")

    def _initialize_servo(self, i2c_id, motor_id):
        """Initialize a servo on a specific PCA9685 controller channel."""
        try:
            servo_motor = servo.Servo(self.pca_controllers[i2c_id].channels[motor_id], min_pulse=500, max_pulse=2500)
            self.servos[(i2c_id, motor_id)] = servo_motor
            logging.info(f"Initialized servo on i2c_id {i2c_id}, motor_id {motor_id}")
        except Exception as e:
            logging.error(f"Failed to initialize servo on i2c_id {i2c_id}, motor_id {motor_id}: {e}")

    def set_servo_angle(self, i2c_id, motor_id, angle):
        """Set the angle of a specific servo."""
        servo_key = (i2c_id, motor_id)
        if servo_key in self.servos:
            try:
                self.servos[servo_key].angle = max(0, min(180, angle))  # Clamp angle to [0, 180]
                logging.info(f"Set servo angle to {angle}° on i2c_id {i2c_id}, motor_id {motor_id}")
            except Exception as e:
                logging.error(f"Failed to set servo angle on i2c_id {i2c_id}, motor_id {motor_id}: {e}")
        else:
            logging.warning(f"Servo not found for i2c_id {i2c_id}, motor_id {motor_id}")

    def set_multiple_servo_angles(self, servos_data):
        """
        Set angles for multiple servos simultaneously.

        servos_data: list of dicts with keys:
            - 'i2c_id': I2C identifier of the servo
            - 'motor_id': Motor channel ID
            - 'angle': Target angle in degrees
        """
        for data in servos_data:
            i2c_id, motor_id, angle = data['i2c_id'], data['motor_id'], data['angle']
            self.set_servo_angle(i2c_id, motor_id, angle)
        logging.info("Completed setting multiple servo angles.")

    def shutdown(self):
        """Deinitialize all PCA9685 controllers to ensure a safe shutdown."""
        for pca in self.pca_controllers.values():
            pca.deinit()
        logging.info("Servo controllers safely deinitialized.")
