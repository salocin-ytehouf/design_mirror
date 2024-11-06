# Face Tracking Pan-Tilt System Using RealSense, YOLO, and Raspberry Pi

This project implements a face tracking system using an Intel RealSense camera, YOLO object detection, and multiple pan-tilt servo motors controlled via a Raspberry Pi. The system detects faces in real-time, computes the necessary pan and tilt angles for each servo motor to point towards the detected face, and controls the pan-tilt units accordingly.

## Table of Contents

- [Introduction](#introduction)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
  - [1. Setting Up the Local Computer](#1-setting-up-the-local-computer)
    - [Installing Intel RealSense SDK](#installing-intel-realsense-sdk)
    - [Setting Up Python Environment](#setting-up-python-environment)
    - [Installing Dependencies](#installing-dependencies)
    - [Configuring the System](#configuring-the-system)
  - [2. Setting Up the Raspberry Pi](#2-setting-up-the-raspberry-pi)
    - [Hardware Connections](#hardware-connections)
    - [Installing Required Libraries](#installing-required-libraries)
    - [Configuring the Raspberry Pi](#configuring-the-raspberry-pi)
- [Usage](#usage)
  - [Running the System](#running-the-system)
- [Code Overview](#code-overview)
  - [Local Computer Modules](#local-computer-modules)
  - [Raspberry Pi Modules](#raspberry-pi-modules)
- [Configuration Details](#configuration-details)
- [Testing and Calibration](#testing-and-calibration)
- [Notes and Considerations](#notes-and-considerations)
- [Troubleshooting](#troubleshooting)
- [Acknowledgments](#acknowledgments)

---

## Introduction

This project creates an interactive system where multiple pan-tilt units track a human face detected by an Intel RealSense camera. The system utilizes:

- **Intel RealSense Camera**: Captures RGB and depth data.
- **YOLO Object Detection**: Detects faces in real-time.
- **Coordinate Transformations**: Calculates transformations between the camera frame and pan-tilt units.
- **MQTT Communication**: Sends computed angles from the local computer to the Raspberry Pi.
- **Raspberry Pi with PCA9685 Servo Drivers**: Controls multiple servos based on received MQTT messages.

---

## Hardware Requirements

- **Local Computer**: Ubuntu PC and  Raspberry Pi.
- **Intel RealSense Depth Camera**: e.g., D435i.
- **Raspberry Pi**: For controlling servos (Model 3B+ or later recommended).
- **PCA9685 Servo Drivers**: Up to three boards for controlling up to 48 servos.
- **Servos**: Standard hobby servos for pan-tilt units.
- **External Power Supply**: To power the servos (e.g., 5V DC supply capable of supplying sufficient current).
- **Jumper Wires and Connectors**: For hardware connections.

---

## Software Requirements

- **Python**: Version 3.8 or later.
- **Realsense SDK**: install on local cumputer.
- **MQTT Broker**: Mosquitto (installed both on local commputer and  Raspberry Pi).
- **Python Libraries**: Listed in the `requirements.txt` file.

---

## Project Structure
```

├── config.yaml
├── main.py
├── models
│   └── best_ncnn_model
│       ├── metadata.yaml
│       ├── model.ncnn.bin
│       ├── model.ncnn.param
│       └── model_ncnn.py
├── modules
│   ├── camera.py
│   ├── detection.py
│   ├── pan_tilt.py
│   ├── processing.py
│   ├── __pycache__
│   │   ├── camera.cpython-38.pyc
│   │   ├── detection.cpython-38.pyc
│   │   ├── pan_tilt.cpython-38.pyc
│   │   ├── processing.cpython-38.pyc
│   │   ├── utils.cpython-38.pyc
│   │   └── visualization.cpython-38.pyc
│   ├── utils.py
│   └── visualization.py
├── pi
│   ├── mqtt_subscriber.py
│   └── servo_controller.py
├── README.md
├── requirements.txt

```


---

## Installation and Setup

Clone or Download the Project Repository to your local computer.

### 1. Setting Up the Local Computer

#### Installing Intel RealSense SDK
installation on local computer 

1. **Update the System**

```bash
   sudo apt-get update
   sudo apt-get upgrade
```
2. **Install Dependencies**

```bash

sudo apt-get install git cmake build-essential libssl-dev libusb-1.0-0-dev pkg-config libgtk-3-dev

```
3. **Clone the Repository**
```bash
git clone https://github.com/IntelRealSense/librealsense.git
```

4. **Run the Installation Script**


```bash

cd librealsense
sudo ./scripts/setup_udev_rules.sh
sudo ./scripts/patch-realsense-ubuntu-lts.sh
```
5. **Build and Install the SDK**


```bash

mkdir build && cd build
cmake ../ -DCMAKE_BUILD_TYPE=Release
make -j4
sudo make install

```
6. **Verify Installation**

Run the RealSense Viewer:

```bash

    realsense-viewer
```
Ensure that your camera is detected and streaming.

#### Setting Up Python Environment
1. **Install Virtual Environment**

```bash

sudo apt-get install python3-venv
```

2. **Create and Activate Virtual Environment**
```bash

python3 -m venv venv
source venv/bin/activate
```
`
#### Installing Dependencies

Install the required Python packages:

```bash

pip install -r requirements.txt
```

Note: Ensure requirements.txt includes all necessary packages:
```
pyrealsense2
opencv-python
numpy
PyYAML
ultralytics
pyvista
matplotlib
paho-mqtt
```

#### Configuring the System

- Edit config.yaml to match your setup (see Configuration Details).
- Ensure the Raspberry Pi's IP Address is correctly set in the code where MQTT communication is established.

### 2. Setting Up the Raspberry Pi

#### Hardware Connections

Enable I2C on Raspberry Pi

```bash
sudo raspi-config
```
Navigate to Interface Options > I2C > Enable

#### Wire the PCA9685 Boards
- VCC (3.3V Logic Power): Connect to Raspberry Pi's 3.3V pin.
- GND: Connect to Raspberry Pi's GND pin.
- SDA and SCL: Connect to Raspberry Pi's SDA (GPIO 2) and SCL (GPIO 3).
- V+ (Servo Power): Connect to external 5V power supply.
- Servos: Connect to PCA9685 channels.

Set Unique I2C Addresses
  Configure each PCA9685 board to have a unique address (e.g., 0x40, 0x41, 0x42) by adjusting the A0–A5 address pins.

#### Installing Required Libraries

Install necessary Python libraries:

```bash

sudo apt-get update
sudo apt-get install python3-pip
pip3 install paho-mqtt pyyaml adafruit-circuitpython-pca9685 adafruit-circuitpython-motor
```

#### Configuring the Raspberry Pi

Install MQTT Broker:
```bash
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

Configure Mosquitto to Accept External Connections:

Edit the Mosquitto configuration file to allow external connections:
```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Add the following lines:
```yaml
listener 1883
allow_anonymous true
```

Restart Mosquitto:
```bash
sudo systemctl restart mosquitto
```

Copy Raspberry Pi Code:
- Copy `pi/mqtt_subscriber.py` and `pi/servo_controller.py` to the Raspberry Pi.

Edit `config.yaml` on Raspberry Pi:
- Ensure that the `config.yaml` file on the Raspberry Pi matches the one on your local computer, especially the `i2c_id` and `motors_id` configurations.

(Additional sections like "Usage" and "Testing" would continue in a similar detailed structure.)


## Usage

### Running the System

#### 1. Start the MQTT Subscriber on Raspberry Pi

```bash
python3 mqtt_subscriber.py
```

This script will listen for incoming MQTT messages and control the servos accordingly.

#### 2. Run the Main Script on Local Computer

```bash
python3 main.py
```
main.py will failed if the rpi is not detected on the network

This script will:

- Initialize the RealSense camera and YOLO model.
- Detect faces and compute pan-tilt angles.
- Send computed angles to the Raspberry Pi via MQTT.

#### 3. Observe the System

- The pan-tilt units should move to track detected faces.
- The console will display logging information about detections and actions.

### Code Overview

#### Local Computer Modules

- **main.py**: The main script that orchestrates camera capture, face detection, angle computation, and MQTT communication.
- **modules/**:
    - **camera.py**: Manages RealSense camera initialization and frame acquisition.
    - **detection.py**: Contains the YOLODetector class for face detection.
    - **processing.py**: Handles coordinate transformations and angle calculations.
    - **pan_tilt.py**: Manages pan-tilt unit configurations and angle broadcasting over MQTT.
    - **utils.py**: Utility functions.
    - **visualization.py**: Functions for visualizing detections (if needed).

#### Raspberry Pi Modules

- **mqtt_subscriber.py**: Subscribes to MQTT messages, parses incoming angle data, and commands the servos.
- **servo_controller.py**: Defines the ServoController class for initializing and controlling multiple PCA9685 boards and servos.

### Configuration Details

#### config.yaml

```yaml
camera:
  position: [0.0, 0.0, 0.0]        # Camera position (origin)
  orientation: [0.0, 0.0, 0.0]     # Camera orientation (no rotation)

pan_tilt_units:
  - name: "PanTilt1"
    position: [0.10, 0.0, 0.0]     # Position relative to camera
    orientation: [0.0, 0.0, 0.0]   # Orientation relative to camera
    i2c_id: 0                      # I2C bus ID
    motors_id: [0, 1]              # Servo channels on PCA9685

  - name: "PanTilt2"
    position: [-0.10, 0.0, 0.0]
    orientation: [0.0, 0.0, 0.0]
    i2c_id: 0
    motors_id: [2, 3]

  # Add additional pan-tilt units as needed
```

- **Positions**: In meters, relative to the camera's coordinate frame.
- **Orientations**: In degrees [roll, pitch, yaw], relative to the camera's frame.
- **i2c_id**: Identifies the PCA9685 board (adjust based on I2C addresses).
- **motors_id**: Servo channels on the PCA9685 board.

### Testing and Calibration

- **Test Individual Components**:
    - Verify the RealSense camera is functioning using `realsense-viewer`.
    - Test the YOLO face detection separately.
    - On the Raspberry Pi, test servo movement with a simple script to ensure servos respond correctly.

- **Calibrate Servos**:
    - Adjust `min_pulse` and `max_pulse` in `servo_controller.py` if servos do not reach full range.
    - Ensure servos are mechanically centered.

- **Verify MQTT Communication**:
    - Use `mosquitto_sub` and `mosquitto_pub` to test MQTT messages between the local computer and Raspberry Pi.

- **Adjust Configurations**:
    - Fine-tune positions and orientations in `config.yaml` for accurate tracking.
    - Check that `i2c_id` and `motors_id` correctly map to your hardware setup.

### Notes and Considerations

- **Power Supply**: Use a sufficient power supply for servos to prevent brownouts.
- **Servo Limits**: Ensure that the computed angles do not exceed the physical limits of your servos.
- **Latency**: Network delays can affect real-time performance. Use a wired connection if possible.
- **Error Handling**: The code includes logging to help identify issues. Check logs if the system isn't behaving as expected.
- **Safety**: Be cautious when working with servos to prevent injury or damage.

### Troubleshooting

- **No MQTT Messages Received**:
    - Ensure the MQTT broker is running on the Raspberry Pi.
    - Check network connectivity between the local computer and Raspberry Pi.
    - Verify that the MQTT topic names match.

- **Servos Not Moving**:
    - Check power connections to the PCA9685 boards.
    - Verify that `i2c_id` and `motors_id` are correctly configured.
    - Use `i2cdetect -y 1` on the Raspberry Pi to ensure PCA9685 boards are detected.

- **Camera Not Detected**:
    - Ensure the Intel RealSense SDK is properly installed.
    - Try different USB ports or cables.

- **Incorrect Tracking**:
    - Recalibrate positions and orientations in `config.yaml`.
    - Verify that coordinate transformations are correctly implemented.

### Acknowledgments

- **Intel RealSense SDK**: For providing libraries to interface with RealSense cameras.
- **Ultralytics YOLO**: For the object detection framework.
- **Adafruit**: For the PCA9685 Python library and motor control libraries.
- **paho-mqtt**: For MQTT client libraries in Python.


### Quick Start Summary

1. **Set Up Hardware**:
    - Connect the Intel RealSense camera to your local computer.
    - Wire the Raspberry Pi with PCA9685 boards and servos.
    - Ensure all devices are powered correctly.

2. **Install Software on Local Computer**:
    - Install Intel RealSense SDK.
    - Set up Python environment and install dependencies.
    - Configure `config.yaml`.

3. **Install Software on Raspberry Pi**:
    - Enable I2C and install required Python libraries.
    - Install and configure MQTT broker.
    - Copy `mqtt_subscriber.py` and `servo_controller.py` to the Raspberry Pi.


4. **Run the System**:
    - Start the MQTT subscriber on the Raspberry Pi.
    - Run `main.py` on your local computer.
    - Observe the pan-tilt units tracking detected faces.

# TO DO 
- add rpi ip adress inside config file 
- sent config file from local computer to rpi 
  - Goal : avoid duplicate config file in local computer and rpi
- allow sequences to move servo (not only face tracking mode)