# mqtt_subscriber.py

import json
import logging
import paho.mqtt.client as mqtt
import yaml
from servo_controller import ServoController

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

# Initialize ServoController
config = load_config('config.yaml')
servo_controller = ServoController(config['pan_tilt_units'])

# Configure MQTT
MQTT_BROKER = 'localhost'  # Update if needed
MQTT_PORT = 1883
MQTT_TOPIC = 'pan_tilt/all_angles'

# Callback function to handle incoming messages
def on_message(client, userdata, msg):
    try:
        message = json.loads(msg.payload.decode())
        units = message.get("units", [])
        logging.info('Received angles for units')

        servos_data = []
        for unit_data in units:
            unit_name = unit_data["unit"]
            i2c_id = unit_data["i2c_id"]
            motors_id = unit_data["motors_id"]
            pan = unit_data["pan"]
            tilt = unit_data["tilt"]

            logging.info(f"Received for {unit_name}: Pan = {pan}°, Tilt = {tilt}°")

            # Prepare data for moving servos
            # Assuming motors_id[0] is pan servo, motors_id[1] is tilt servo
            servos_data.append({
                'i2c_id': i2c_id,
                'motor_id': motors_id[0],
                'angle': pan
            })
            servos_data.append({
                'i2c_id': i2c_id,
                'motor_id': motors_id[1],
                'angle': tilt
            })

        # Move servos
        if servos_data:
            servo_controller.move_multiple_servos(servos_data)
    except Exception as e:
        logging.error(f"Error processing message: {e}")

# Initialize MQTT client
client = mqtt.Client()
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.subscribe(MQTT_TOPIC)
    logging.info(f"Subscribed to MQTT topic '{MQTT_TOPIC}' on broker '{MQTT_BROKER}:{MQTT_PORT}'")
except Exception as e:
    logging.error(f"Failed to connect to MQTT broker: {e}")
    exit(1)

# Start MQTT loop
try:
    client.loop_forever()
except KeyboardInterrupt:
    logging.info("MQTT subscriber interrupted by user.")
except Exception as e:
    logging.error(f"MQTT loop error: {e}")
finally:
    client.disconnect()
    logging.info("MQTT client disconnected.")
