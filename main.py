#!/usr/bin/env python3
"""
Train Video Processing System
Processes train videos to split coaches, extract frames, detect components, and generate reports.
"""

import cv2
import numpy as np
import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any
from tqdm import tqdm
import logging
from datetime import datetime

from utils.video_processor import VideoProcessor
from utils.frame_extractor import FrameExtractor
from utils.component_detector import ComponentDetector
from utils.report_generator import ReportGenerator
from utils.folder_manager import FolderManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrainVideoProcessor:
    """Main class for processing train videos."""
    
    def __init__(self, input_dir: str, output_dir: str = "Processed_Video"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.video_processor = VideoProcessor()
        self.frame_extractor = FrameExtractor()
        self.component_detector = ComponentDetector()
        self.report_generator = ReportGenerator()
        self.folder_manager = FolderManager()
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
    def process_all_videos(self) -> Dict[str, Any]:
        """Process all videos in the input directory."""
        video_files = list(self.input_dir.glob("*.mp4")) + list(self.input_dir.glob("*.avi")) + list(self.input_dir.glob("*.mov"))
        
        if not video_files:
            logger.error(f"No video files found in {self.input_dir}")
            return {}
        
        all_results = {}
        
        for video_path in tqdm(video_files, desc="Processing videos"):
            logger.info(f"Processing video: {video_path.name}")
            try:
                results = self.process_single_video(video_path)
                all_results[video_path.stem] = results
            except Exception as e:
                logger.error(f"Error processing {video_path.name}: {str(e)}")
                continue
        
        # Generate master report
        self.report_generator.generate_master_report(all_results, self.output_dir)
        
        return all_results
    
    def process_single_video(self, video_path: Path) -> Dict[str, Any]:
        """Process a single video file."""
        # Extract train number from filename (assuming format like "12309.mp4")
        train_number = video_path.stem
        
        # Step 1: Split video into coaches
        logger.info(f"Splitting video {train_number} into coaches...")
        coach_clips = self.video_processor.split_video_into_coaches(str(video_path))
        
        results = {
            'train_number': train_number,
            'total_coaches': len(coach_clips),
            'coaches': []
        }
        
        # Step 2: Process each coach
        for i, (coach_filename, coach_info) in enumerate(coach_clips.items(), 1):
            logger.info(f"Processing coach {i}/{len(coach_clips)}")
            
            coach_path = coach_info.get('path')
            if not coach_path or not os.path.exists(coach_path):
                logger.error(f"Coach video not found: {coach_path}")
                continue
            
            # Create coach folder
            coach_folder = self.folder_manager.create_coach_folder(
                self.output_dir, train_number, i
            )
            
            # Step 3: Extract key frames with 10% similarity rule
            frames = self.frame_extractor.extract_key_frames(
                coach_path, similarity_threshold=0.9
            )
            
            # Step 4: Detect components
            components = self.component_detector.detect_components(coach_path, frames)
            
            # Step 5: Save frames and annotations
            self.folder_manager.save_coach_data(
                coach_folder, coach_path, frames, components, train_number, i
            )
            
            # Store results
            coach_data = {
                'coach_number': i,
                'coach_type': coach_info.get('type', 'wagon'),
                'frame_count': len(frames),
                'components': components,
                'doors_open': components.get('doors_open', 0),
                'doors_closed': components.get('doors_closed', 0)
            }
            results['coaches'].append(coach_data)
        
        return results

def main():
    """Main function to run the video processing system."""
    # Configuration
    INPUT_DIR = "input_videos"  # Directory containing train videos
    OUTPUT_DIR = "Processed_Video"
    
    # Check if input directory exists
    if not os.path.exists(INPUT_DIR):
        logger.error(f"Input directory '{INPUT_DIR}' not found!")
        logger.info("Please create the directory and add your train videos.")
        return
    
    # Initialize processor
    processor = TrainVideoProcessor(INPUT_DIR, OUTPUT_DIR)
    
    # Process all videos
    logger.info("Starting video processing...")
    results = processor.process_all_videos()
    
    logger.info(f"Processing complete! Results saved to {OUTPUT_DIR}")
    logger.info(f"Processed {len(results)} videos")

if __name__ == "__main__":
    main()
