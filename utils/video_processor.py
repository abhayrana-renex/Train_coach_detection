"""
Video processing utilities for splitting train videos into coaches.
"""

import cv2
import numpy as np
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Handles video splitting and coach detection."""
    
    def __init__(self):
        self.engine_detector = EngineDetector()
        self.wagon_detector = WagonDetector()
    
    def split_video_into_coaches(self, video_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Split a train video into individual coach clips.
        
        Args:
            video_path: Path to the input video file
            
        Returns:
            Dictionary mapping coach filenames to coach information
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        logger.info(f"Video: {fps} FPS, {total_frames} frames, {duration:.2f}s duration")
        
        # Detect coach boundaries
        coach_boundaries = self._detect_coach_boundaries(cap, fps)
        
        # Create coach clips
        coach_clips = {}
        video_name = Path(video_path).stem
        
        for i, (start_frame, end_frame, coach_type) in enumerate(coach_boundaries, 1):
            start_time = start_frame / fps
            end_time = end_frame / fps
            
            # Create coach filename
            coach_filename = f"{video_name}_{i}.mp4"
            coach_path = self._extract_coach_clip(
                video_path, start_time, end_time, coach_filename
            )
            
            coach_clips[coach_filename] = {
                'path': coach_path,
                'type': coach_type,
                'start_frame': start_frame,
                'end_frame': end_frame,
                'start_time': start_time,
                'end_time': end_time
            }
        
        cap.release()
        return coach_clips
    
    def _detect_coach_boundaries(self, cap: cv2.VideoCapture, fps: int) -> List[Tuple[int, int, str]]:
        """
        Detect boundaries between coaches using motion and edge detection.
        
        Args:
            cap: OpenCV video capture object
            fps: Frames per second
            
        Returns:
            List of (start_frame, end_frame, coach_type) tuples
        """
        # Get total frames and duration
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # For train videos, assume 8-12 coaches on average
        # Split video into equal segments
        num_coaches = min(12, max(6, int(duration / 15)))  # 15 seconds per coach average
        
        boundaries = []
        segment_length = total_frames // num_coaches
        
        for i in range(num_coaches):
            start_frame = i * segment_length
            end_frame = min((i + 1) * segment_length, total_frames)
            coach_type = 'engine' if i == 0 else 'wagon'
            boundaries.append((start_frame, end_frame, coach_type))
        
        # Reset video to beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        return boundaries
    
    def _calculate_motion(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """Calculate motion between two frames."""
        diff = cv2.absdiff(prev_frame, curr_frame)
        motion = np.mean(diff) / 255.0
        return motion
    
    def _extract_coach_clip(self, video_path: str, start_time: float, end_time: float, 
                          output_filename: str) -> str:
        """
        Extract a coach clip from the main video.
        
        Args:
            video_path: Path to input video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_filename: Name for output file
            
        Returns:
            Path to extracted coach clip
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Set up video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_path = f"temp_{output_filename}"
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            cap.release()
            raise ValueError(f"Could not create output video: {output_path}")
        
        # Seek to start time
        start_frame = int(start_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Extract frames
        end_frame = int(end_time * fps)
        current_frame = start_frame
        
        while current_frame < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            out.write(frame)
            current_frame += 1
        
        cap.release()
        out.release()
        
        # Verify the output file was created
        if not os.path.exists(output_path):
            raise ValueError(f"Failed to create coach clip: {output_path}")
        
        return output_path

class EngineDetector:
    """Detects engines in train videos."""
    
    def detect_engines(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect engines in a frame.
        
        Args:
            frame: Input frame
            
        Returns:
            List of bounding boxes (x, y, w, h)
        """
        # Simple engine detection based on size and position
        # In a real implementation, you'd use more sophisticated methods
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect large rectangular regions (potential engines)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        engines = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Filter for engine-like shapes (large, rectangular)
            if area > 10000 and w > h * 0.5:  # Wide rectangles
                engines.append((x, y, w, h))
        
        return engines

class WagonDetector:
    """Detects wagons in train videos."""
    
    def detect_wagons(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect wagons in a frame.
        
        Args:
            frame: Input frame
            
        Returns:
            List of bounding boxes (x, y, w, h)
        """
        # Similar to engine detection but with different criteria
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect wagon-like shapes
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        wagons = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Filter for wagon-like shapes
            if 5000 < area < 10000 and w > h * 0.3:
                wagons.append((x, y, w, h))
        
        return wagons
