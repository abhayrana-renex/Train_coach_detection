"""
Frame extraction utilities with similarity-based selection.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any
import logging
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)

class FrameExtractor:
    """Handles frame extraction with similarity-based selection."""
    
    def __init__(self):
        self.reference_frame = None
        self.similarity_threshold = 0.9
    
    def extract_key_frames(self, video_path: str, similarity_threshold: float = 0.9, 
                          target_frames: int = 8) -> List[np.ndarray]:
        """
        Extract key frames from a video using similarity-based selection.
        
        Args:
            video_path: Path to the video file
            similarity_threshold: Threshold for frame similarity (0.9 = 90% similar)
            target_frames: Target number of frames to extract
            
        Returns:
            List of extracted frames
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        frames = []
        frame_count = 0
        reference_frame = None
        
        # Get total frames for progress tracking
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # Sample every N frames to reduce computation
        sample_interval = max(1, total_frames // (target_frames * 3))
        
        logger.info(f"Extracting frames from {video_path}")
        logger.info(f"Total frames: {total_frames}, Sample interval: {sample_interval}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample frames at intervals
            if frame_count % sample_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if reference_frame is None:
                    # First frame becomes reference
                    reference_frame = gray.copy()
                    frames.append(frame.copy())
                    logger.info(f"Added reference frame at {frame_count}")
                else:
                    # Calculate similarity with reference frame
                    similarity = self._calculate_similarity(reference_frame, gray)
                    
                    if similarity < similarity_threshold:
                        # Significant change detected, save previous frame
                        frames.append(frame.copy())
                        reference_frame = gray.copy()
                        logger.info(f"Added frame at {frame_count}, similarity: {similarity:.3f}")
                        
                        # Stop if we have enough frames
                        if len(frames) >= target_frames:
                            break
            
            frame_count += 1
        
        cap.release()
        
        # Ensure we have at least some frames
        if len(frames) == 0:
            logger.warning("No frames extracted, using first frame")
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
            cap.release()
        
        logger.info(f"Extracted {len(frames)} key frames")
        return frames
    
    def _calculate_similarity(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """
        Calculate structural similarity between two frames.
        
        Args:
            frame1: First frame (grayscale)
            frame2: Second frame (grayscale)
            
        Returns:
            Similarity score between 0 and 1 (1 = identical)
        """
        try:
            # Ensure frames are the same size
            if frame1.shape != frame2.shape:
                frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
            
            # Calculate SSIM
            similarity = ssim(frame1, frame2, data_range=255)
            return max(0, similarity)  # Ensure non-negative
        except Exception as e:
            logger.warning(f"Error calculating similarity: {e}")
            return 0.0
    
    def extract_frames_at_timestamps(self, video_path: str, timestamps: List[float]) -> List[np.ndarray]:
        """
        Extract frames at specific timestamps.
        
        Args:
            video_path: Path to the video file
            timestamps: List of timestamps in seconds
            
        Returns:
            List of extracted frames
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frames = []
        
        for timestamp in timestamps:
            frame_number = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
            else:
                logger.warning(f"Could not extract frame at timestamp {timestamp}")
        
        cap.release()
        return frames
    
    def extract_uniform_frames(self, video_path: str, num_frames: int = 8) -> List[np.ndarray]:
        """
        Extract frames uniformly distributed across the video.
        
        Args:
            video_path: Path to the video file
            num_frames: Number of frames to extract
            
        Returns:
            List of extracted frames
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = total_frames // num_frames
        
        frames = []
        for i in range(num_frames):
            frame_number = i * frame_interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        
        cap.release()
        return frames
    
    def save_frames(self, frames: List[np.ndarray], output_dir: Path, 
                   prefix: str = "frame") -> List[str]:
        """
        Save frames to disk.
        
        Args:
            frames: List of frames to save
            output_dir: Directory to save frames
            prefix: Prefix for frame filenames
            
        Returns:
            List of saved frame paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_paths = []
        
        for i, frame in enumerate(frames, 1):
            filename = f"{prefix}_{i:03d}.jpg"
            filepath = output_dir / filename
            
            cv2.imwrite(str(filepath), frame)
            saved_paths.append(str(filepath))
        
        logger.info(f"Saved {len(frames)} frames to {output_dir}")
        return saved_paths
