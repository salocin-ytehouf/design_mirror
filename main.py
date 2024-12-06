# main.py

import time
import cv2
import os
import logging
import traceback

from modules.camera import RealSenseCamera
from modules.detection import YOLODetector
from modules.processing import get_closest_face
from modules.visualization import display_frames
from modules.pan_tilt import PanTiltUnitManager
from modules.utils import load_config_file, transfer_config
import pyrealsense2 as rs

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    # Load configuration
    try:
        config = load_config_file('config.yaml')
    except Exception as e:
        logging.error("Failed to load configuration:")
        logging.error(traceback.format_exc())  # Log full stack trace
        return
    
    # transfer config file to the rpi
    try:
        transfer_config(config)
    except Exception as e:
        logging.error("Failed to export configuration to rpi:")
        logging.error(traceback.format_exc())  # Log full stack trace
        return

    # Initialize components
    try:
        camera = RealSenseCamera()
        detector = YOLODetector(model_path='models/best_ncnn_model')
        pan_tilt_manager = PanTiltUnitManager(
            config['pan_tilt_units'],
            mqtt_broker=config['rpi']['ip'],
            mqtt_port=1883,
            angle_min = int(config["angle_limits"]["min_angle"]),
            angle_max = int(config["angle_limits"]["max_angle"]))

    except Exception as e:
        logging.error("Initialization error:")
        logging.error(traceback.format_exc())  # Log full stack trace
        return

    try:
        while True:
            # Get aligned frames
            depth_frame, depth_image, color_image, depth_intrin = camera.get_frames()
            if depth_frame is None or color_image is None:
                continue

            # Run YOLO detection
            try:
                faces = detector.detect_faces(color_image)
            except Exception as e:
                #logging.error(f"Face detection error: {e}")
                logging.error(traceback.format_exc())
                exit()
                continue

            # Get face positions in 3D space
            frame_face_positions = []
            os.system("clear")
            for face in faces:
                u, v = int(face[0]), int(face[1])
                try:
                    # Use get_distance() on the depth_frame object
                    depth = depth_frame.get_distance(u, v)
                    x, y, z = rs.rs2_deproject_pixel_to_point(depth_intrin, [u, v], depth)
                    logging.debug(f"3D coordinates at pixel ({u}, {v}): x={x:.3f}m, y={y:.3f}m, z={z:.3f}m")
                    frame_face_positions.append([x, y, z])

                    # Draw on frames
                    detector.draw_face_marker(color_image, (u, v))
                except Exception as e:
                    logging.error(f"Error processing face at pixel ({u}, {v}):")
                    logging.error(traceback.format_exc())  # Log full stack trace
                    continue


            # Get the closest face
            closest_face = get_closest_face(frame_face_positions)
            if closest_face:
                logging.info(f"Closest face coordinates: x={closest_face[0]:.3f}m, y={closest_face[1]:.3f}m, z={closest_face[2]:.3f}m")

                # Compute pan and tilt angles for each pan-tilt unit
                pan_tilt_manager.compute_and_send_all_angles(closest_face)
            else:
                logging.info("No faces detected.")

            # Display frames
            display_frames(color_image)

            # Break loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        logging.error(traceback.format_exc())
        exit()
    finally:
        camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
