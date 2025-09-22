"""
Component detection utilities for train coaches.
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ComponentDetector:
    """Detects components like doors, engines, and wagons in train frames."""
    
    def __init__(self):
        self.door_detector = DoorDetector()
        self.engine_detector = EngineDetector()
        self.wagon_detector = WagonDetector()
    
    def detect_components(self, video_path: str, frames: List[np.ndarray]) -> Dict[str, Any]:
        """
        Detect components in video frames.
        
        Args:
            video_path: Path to the video file
            frames: List of frames to analyze
            
        Returns:
            Dictionary containing detected components
        """
        components = {
            'doors_open': 0,
            'doors_closed': 0,
            'engines': [],
            'wagons': [],
            'annotations': []
        }
        
        for i, frame in enumerate(frames):
            # Detect doors
            doors = self.door_detector.detect_doors(frame)
            components['doors_open'] += doors['open']
            components['doors_closed'] += doors['closed']
            
            # Detect engines
            engines = self.engine_detector.detect_engines(frame)
            components['engines'].extend(engines)
            
            # Detect wagons
            wagons = self.wagon_detector.detect_wagons(frame)
            components['wagons'].extend(wagons)
            
            # Create annotations
            annotated_frame = self._annotate_frame(frame, doors, engines, wagons)
            components['annotations'].append({
                'frame_index': i,
                'annotated_frame': annotated_frame,
                'doors': doors,
                'engines': engines,
                'wagons': wagons
            })
        
        return components
    
    def _annotate_frame(self, frame: np.ndarray, doors: Dict, engines: List, 
                       wagons: List) -> np.ndarray:
        """Annotate frame with detected components."""
        annotated = frame.copy()
        
        # Draw door annotations
        for door in doors.get('door_boxes', []):
            x, y, w, h = door['bbox']
            color = (0, 255, 0) if door['status'] == 'open' else (0, 0, 255)
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            cv2.putText(annotated, f"Door: {door['status']}", 
                       (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Draw engine annotations
        for engine in engines:
            x, y, w, h = engine
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(annotated, "Engine", (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        # Draw wagon annotations
        for wagon in wagons:
            x, y, w, h = wagon
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 255), 2)
            cv2.putText(annotated, "Wagon", (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        return annotated

class DoorDetector:
    """Detects doors in train frames."""
    
    def detect_doors(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Detect doors in a frame.
        
        Args:
            frame: Input frame
            
        Returns:
            Dictionary with door information
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Use edge detection to find door-like structures
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        doors = {'open': 0, 'closed': 0, 'door_boxes': []}
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Filter for door-like shapes (rectangular, certain size)
            if 1000 < area < 10000 and w > h * 0.3 and w < h * 3:
                # Determine if door is open or closed based on internal features
                door_status = self._classify_door_status(frame[y:y+h, x:x+w])
                
                door_info = {
                    'bbox': (x, y, w, h),
                    'status': door_status,
                    'area': area
                }
                doors['door_boxes'].append(door_info)
                
                if door_status == 'open':
                    doors['open'] += 1
                else:
                    doors['closed'] += 1
        
        return doors
    
    def _classify_door_status(self, door_roi: np.ndarray) -> str:
        """
        Classify if a door is open or closed.
        
        Args:
            door_roi: Region of interest containing the door
            
        Returns:
            'open' or 'closed'
        """
        if door_roi.size == 0:
            return 'closed'
        
        # Convert to grayscale if needed
        if len(door_roi.shape) == 3:
            gray = cv2.cvtColor(door_roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = door_roi
        
        # Calculate variance - open doors typically have more variation
        variance = np.var(gray)
        
        # Simple heuristic: higher variance suggests open door
        threshold = 1000
        return 'open' if variance > threshold else 'closed'

class EngineDetector:
    """Detects engines in train frames."""
    
    def detect_engines(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect engines in a frame.
        
        Args:
            frame: Input frame
            
        Returns:
            List of bounding boxes (x, y, w, h)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Use template matching or feature detection for engines
        # For now, use simple contour detection
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        engines = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Engines are typically large and rectangular
            if area > 15000 and w > h * 0.5:
                engines.append((x, y, w, h))
        
        return engines

class WagonDetector:
    """Detects wagons in train frames."""
    
    def detect_wagons(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect wagons in a frame.
        
        Args:
            frame: Input frame
            
        Returns:
            List of bounding boxes (x, y, w, h)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Similar to engine detection but with different criteria
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        wagons = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Wagons are typically medium-sized and rectangular
            if 5000 < area < 15000 and w > h * 0.3:
                wagons.append((x, y, w, h))
        
        return wagons
