# modules/detection.py

import cv2
import numpy as np
import logging
from ultralytics import YOLO

class YOLODetector:
    def __init__(self, model_path, target_class=1):
        try:
            self.model = YOLO(model_path)
            logging.info(f"YOLO model loaded from {model_path}.")
        except Exception as e:
            logging.error(f"Failed to load YOLO model from {model_path}: {e}")
            raise
        self.target_class = target_class
        self.previous_results = None

    def detect_faces(self, color_image):
        """Run YOLO detection and return filtered bounding boxes and centers."""
        try:
            results = self.model.track(color_image, persist=True)
            self.previous_results = results
            filtered_data = results[0].boxes[results[0].boxes.cls == self.target_class]
            centers = self.get_centers(filtered_data.xywh)
            return centers
        except Exception as e:
            logging.error(f"Error during YOLO detection: {e}")
            raise

    def get_centers(self, bb_list):
        """Get the list of centers for each bounding box."""
        centers = []
        for bb in bb_list:
            x_center, y_center, width, height = bb
            centers.append((x_center.item(), y_center.item()))
        return centers

    def draw_face_marker(self, frame, center):
        """Draw a marker on the detected face."""
        u, v = center
        cv2.circle(frame, (u, v), 10, (0, 255, 0), 2)
