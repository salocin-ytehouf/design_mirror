# modules/camera.py

import pyrealsense2 as rs
import numpy as np
import logging

class RealSenseCamera:
    def __init__(self):
        """Initialize the RealSense camera pipeline and align object."""
        self.pipeline = rs.pipeline()
        self.align = rs.align(rs.stream.color)
        config = rs.config()
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        try:
            self.pipeline.start(config)
            logging.info("RealSense camera pipeline started.")
        except Exception as e:
            logging.error(f"Failed to start RealSense pipeline: {e}")
            raise
        self.depth_intrin = None

        # Initialize post-processing filters
        self.spatial = rs.spatial_filter()
        self.temporal = rs.temporal_filter()
        self.hole_filling = rs.hole_filling_filter()

    def get_frames(self):
        """Retrieve aligned depth and color frames from the RealSense pipeline."""
        try:
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                logging.warning("No frames received from camera.")
                return None, None, None, None

            # Apply filters to depth frame
            depth_frame = self.apply_filters(depth_frame)

            # Convert depth and color frames to NumPy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # Get depth intrinsics
            if not self.depth_intrin:
                self.depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics

            return depth_frame, depth_image, color_image, self.depth_intrin
        except Exception as e:
            logging.error(f"Error retrieving frames: {e}")
            return None, None, None, None

    def apply_filters(self, depth_frame):
        """Apply post-processing filters to the depth frame."""
        try:
            depth_frame = self.spatial.process(depth_frame).as_depth_frame()
            depth_frame = self.temporal.process(depth_frame).as_depth_frame()
            depth_frame = self.hole_filling.process(depth_frame).as_depth_frame()
            return depth_frame
        except Exception as e:
            logging.error(f"Error applying filters to depth frame: {e}")
            raise

    def release(self):
        """Stop the camera pipeline."""
        self.pipeline.stop()
        logging.info("RealSense camera pipeline stopped.")
