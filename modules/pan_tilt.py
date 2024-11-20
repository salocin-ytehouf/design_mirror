# modules/pan_tilt.py

import logging
from .processing import (
    transform_target_realsense_to_ro,
    transform_to_unit_frame,
    compute_pan_tilt_angles,
    transform_angle_to_servo
)
import paho.mqtt.client as mqtt
import json

class PanTiltUnit:
    def __init__(self, name, position, orientation, i2c_id=None, motors_id=None, angle_min=None, angle_max=None):
        self.name = name
        self.position = position  # [x, y, z]
        self.orientation = orientation  # [roll, pitch, yaw]
        self.i2c_id = i2c_id
        self.motors_id = motors_id
        self.angle_min = angle_min
        self.angle_max = angle_max

    def compute_angles(self, target_position):
        """Compute pan and tilt angles to the target."""
        try:
            transformed_position = transform_to_unit_frame(target_position, self.position, self.orientation)
            pan_angle, tilt_angle = compute_pan_tilt_angles(transformed_position)
            # Transform to servo angles
            pan_servo_angle = transform_angle_to_servo(pan_angle, self.angle_min, self.angle_max)
            tilt_servo_angle = transform_angle_to_servo(tilt_angle, self.angle_min, self.angle_max)
            return pan_servo_angle, tilt_servo_angle
        except Exception as e:
            logging.error(f"Error computing angles for {self.name}: {e}")
            return None, None

class PanTiltUnitManager:
    def __init__(self, units_config, mqtt_broker='localhost', mqtt_port=1883, angle_min=None, angle_max=None):
        self.units = []
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(mqtt_broker, mqtt_port)
        self.mqtt_client.loop_start()
        self.angle_min = angle_min
        self.angle_max = angle_max

        for unit_conf in units_config:
            try:
                unit = PanTiltUnit(
                    name=unit_conf['name'],
                    position=unit_conf['position'],
                    orientation=unit_conf['orientation'],
                    i2c_id=unit_conf.get('i2c_id'),
                    motors_id=unit_conf.get('motors_id'),
                    angle_min= self.angle_min,
                    angle_max= self.angle_max,
                )
                self.units.append(unit)
                logging.info(f"Initialized pan-tilt unit: {unit.name}")
            except Exception as e:
                logging.error(f"Error initializing pan-tilt unit {unit_conf.get('name', 'Unknown')}: {e}")

    def compute_and_send_all_angles(self, target_rs):
        """Compute pan-tilt angles for all units and send them in a single MQTT message."""
        # Transform target position to absolute frame
        target_position = transform_target_realsense_to_ro(*target_rs)

        # Collect all servo angles
        all_angles = []
        for unit in self.units:
            pan_servo_angle, tilt_servo_angle = unit.compute_angles(target_position)
            if pan_servo_angle is not None and tilt_servo_angle is not None:
                logging.info(f"{unit.name} -> Pan Servo Angle: {pan_servo_angle:.2f}°, Tilt Servo Angle: {tilt_servo_angle:.2f}°")
                logging.info(f"#################################################################################################")
                # Append the data to the list
                unit_data = {
                    "unit": unit.name,
                    "i2c_id": unit.i2c_id,
                    "motors_id": unit.motors_id,
                    "pan": pan_servo_angle,
                    "tilt": tilt_servo_angle
                }
                all_angles.append(unit_data)
            else:
                logging.warning(f"Could not compute angles for {unit.name}.")

        # Send all angles in a single MQTT message
        if all_angles:
            self.send_all_angles_over_mqtt(all_angles)

    def send_all_angles_over_mqtt(self, all_angles):
        """Send all servo angles over MQTT in a single message."""
        message = {
            "units": all_angles
        }
        self.mqtt_client.publish("pan_tilt/all_angles", json.dumps(message))
        logging.info(f"Sent all angles over MQTT: {json.dumps(message)}")

    def __del__(self):
        """Ensure MQTT client is properly stopped when the manager is deleted."""
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
