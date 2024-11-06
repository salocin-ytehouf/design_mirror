# modules/visualization.py

import cv2

def display_frames(color_image):
    """Display the color frame."""
    cv2.imshow("Face Detection", color_image)
