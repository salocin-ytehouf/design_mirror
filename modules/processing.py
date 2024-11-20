# modules/processing.py

import math
import numpy as np
import logging

def get_closest_face(frame_face_positions):
    """Finds the closest face from a list of 3D positions."""
    if not frame_face_positions:
        logging.debug("No face positions provided to get_closest_face.")
        return None

    min_distance = float('inf')
    closest_face = None

    for face in frame_face_positions:
        x, y, z = face
        distance = math.sqrt(x**2 + y**2 + z**2)

        if distance < min_distance:
            min_distance = distance
            closest_face = face

    logging.debug(f"Closest face found at distance {min_distance:.3f}m.")
    return closest_face

def transform_target_realsense_to_ro(x_rs, y_rs, z_rs):
    """Transform RealSense coordinates to the required coordinate system."""
    x = -x_rs
    y = -y_rs
    z = z_rs
    return x, y, z

def euler_to_rotation_matrix(roll, pitch, yaw):
    """Convert Euler angles to rotation matrix."""
    roll, pitch, yaw = np.radians(roll), np.radians(pitch), np.radians(yaw)
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(roll), -np.sin(roll)],
                    [0, np.sin(roll),  np.cos(roll)]])
    R_y = np.array([[ np.cos(pitch), 0, np.sin(pitch)],
                    [0, 1, 0],
                    [-np.sin(pitch), 0, np.cos(pitch)]])
    R_z = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                    [np.sin(yaw),  np.cos(yaw), 0],
                    [0, 0, 1]])
    return R_z @ R_y @ R_x

def transform_to_unit_frame(target_position, unit_position, unit_orientation):
    """Transform target to pan-tilt unit's frame."""
    R_unit = euler_to_rotation_matrix(*unit_orientation)
    relative_position = np.array(target_position) - np.array(unit_position)
    transformed_position = R_unit.T @ relative_position
    return transformed_position

def compute_pan_tilt_angles(transformed_position):
    """Compute pan and tilt angles."""
    x_rel, y_rel, z_rel = transformed_position
    pan_angle = math.degrees(math.atan2(x_rel, z_rel))
    tilt_angle = math.degrees(math.atan2(y_rel, math.sqrt(x_rel**2 + z_rel**2)))
    return pan_angle, tilt_angle

#######################################################################################
#######################################################################################

'''
def apply_safety_limits(angle):
    """Clamp angle to be within -45 to +45 degrees."""
    return max(-65, min(65, angle))
'''
def apply_safety_limits(angle, min_angle, max_angle):
    """Clamp angle to be within the min and max limits defined in the configuration."""
    return max(min_angle, min(max_angle, angle))

def map_to_servo_range(angle):
    """Map angle from -90 to +90 degrees to 0 to 180 degrees."""
    return angle + 90

def transform_angle_to_servo(angle, min_angle, max_angle):
    """Transform angle to be safe and map to servo range 0 to 180 degrees."""
    # Apply safety limits
    safe_angle = apply_safety_limits(angle, min_angle, max_angle)
    
    # Map to servo range
    servo_angle = map_to_servo_range(safe_angle)
    
    return servo_angle