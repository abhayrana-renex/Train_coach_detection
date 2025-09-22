"""
Folder management utilities for organizing processed video data.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FolderManager:
    """Manages folder structure for processed videos."""
    
    def __init__(self):
        self.base_structure = {
            'frames': 'frames',
            'annotated': 'annotated',
            'coach_video': 'coach_video'
        }
    
    def create_coach_folder(self, base_dir: Path, train_number: str, coach_number: int) -> Path:
        """
        Create folder structure for a coach.
        
        Args:
            base_dir: Base output directory
            train_number: Train number/identifier
            coach_number: Coach number
            
        Returns:
            Path to the created coach folder
        """
        coach_folder = base_dir / f"{train_number}_{coach_number}"
        
        # Create main coach folder
        coach_folder.mkdir(parents=True, exist_ok=True)
        
        # Create subfolders
        for subfolder in self.base_structure.values():
            (coach_folder / subfolder).mkdir(exist_ok=True)
        
        logger.info(f"Created coach folder: {coach_folder}")
        return coach_folder
    
    def save_coach_data(self, coach_folder: Path, coach_video_path: str, 
                       frames: List, components: Dict[str, Any], 
                       train_number: str, coach_number: int) -> None:
        """
        Save all coach data to the folder structure.
        
        Args:
            coach_folder: Path to coach folder
            coach_video_path: Path to coach video file
            frames: List of extracted frames
            components: Detected components
            train_number: Train number
            coach_number: Coach number
        """
        # Save coach video
        coach_video_dest = coach_folder / f"{train_number}_{coach_number}.mp4"
        if os.path.exists(coach_video_path):
            shutil.copy2(coach_video_path, coach_video_dest)
            logger.info(f"Saved coach video: {coach_video_dest}")
        
        # Save frames
        frames_dir = coach_folder / 'frames'
        self._save_frames(frames, frames_dir, train_number, coach_number)
        
        # Save annotated frames
        annotated_dir = coach_folder / 'annotated'
        self._save_annotated_frames(components.get('annotations', []), 
                                  annotated_dir, train_number, coach_number)
        
        # Save component data as JSON
        self._save_component_data(components, coach_folder, train_number, coach_number)
    
    def _save_frames(self, frames: List, frames_dir: Path, train_number: str, coach_number: int) -> None:
        """Save extracted frames."""
        for i, frame in enumerate(frames, 1):
            frame_filename = f"{train_number}_{coach_number}_{i:03d}.jpg"
            frame_path = frames_dir / frame_filename
            
            import cv2
            cv2.imwrite(str(frame_path), frame)
        
        logger.info(f"Saved {len(frames)} frames to {frames_dir}")
    
    def _save_annotated_frames(self, annotations: List[Dict], annotated_dir: Path, 
                              train_number: str, coach_number: int) -> None:
        """Save annotated frames."""
        for i, annotation in enumerate(annotations, 1):
            annotated_frame = annotation.get('annotated_frame')
            if annotated_frame is not None:
                frame_filename = f"{train_number}_{coach_number}_annotated_{i:03d}.jpg"
                frame_path = annotated_dir / frame_filename
                
                import cv2
                cv2.imwrite(str(frame_path), annotated_frame)
        
        logger.info(f"Saved {len(annotations)} annotated frames to {annotated_dir}")
    
    def _save_component_data(self, components: Dict[str, Any], coach_folder: Path, 
                           train_number: str, coach_number: int) -> None:
        """Save component detection data as JSON."""
        import json
        
        component_data = {
            'train_number': train_number,
            'coach_number': coach_number,
            'doors_open': components.get('doors_open', 0),
            'doors_closed': components.get('doors_closed', 0),
            'engines': components.get('engines', []),
            'wagons': components.get('wagons', []),
            'total_components': {
                'doors': components.get('doors_open', 0) + components.get('doors_closed', 0),
                'engines': len(components.get('engines', [])),
                'wagons': len(components.get('wagons', []))
            }
        }
        
        json_path = coach_folder / f"{train_number}_{coach_number}_components.json"
        with open(json_path, 'w') as f:
            json.dump(component_data, f, indent=2)
        
        logger.info(f"Saved component data: {json_path}")
    
    def create_master_folder(self, base_dir: Path) -> Path:
        """Create master folder structure."""
        master_folder = base_dir / "Processed_Video"
        master_folder.mkdir(exist_ok=True)
        
        # Create subfolders
        (master_folder / "reports").mkdir(exist_ok=True)
        (master_folder / "logs").mkdir(exist_ok=True)
        
        return master_folder
    
    def organize_by_train(self, base_dir: Path, results: Dict[str, Any]) -> None:
        """
        Organize results by train number.
        
        Args:
            base_dir: Base output directory
            results: Processing results
        """
        for train_number, train_data in results.items():
            train_folder = base_dir / f"Train_{train_number}"
            train_folder.mkdir(exist_ok=True)
            
            # Move coach folders
            for coach_data in train_data.get('coaches', []):
                coach_number = coach_data['coach_number']
                source_folder = base_dir / f"{train_number}_{coach_number}"
                dest_folder = train_folder / f"Coach_{coach_number}"
                
                if source_folder.exists():
                    shutil.move(str(source_folder), str(dest_folder))
                    logger.info(f"Moved {source_folder} to {dest_folder}")
    
    def cleanup_temp_files(self, base_dir: Path) -> None:
        """Clean up temporary files."""
        temp_files = list(base_dir.glob("temp_*"))
        for temp_file in temp_files:
            try:
                temp_file.unlink()
                logger.info(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_file}: {e}")
    
    def get_folder_structure(self, base_dir: Path) -> Dict[str, Any]:
        """
        Get the current folder structure.
        
        Args:
            base_dir: Base directory to analyze
            
        Returns:
            Dictionary representing folder structure
        """
        structure = {}
        
        for item in base_dir.iterdir():
            if item.is_dir():
                structure[item.name] = self._get_subfolder_structure(item)
            else:
                structure[item.name] = "file"
        
        return structure
    
    def _get_subfolder_structure(self, folder: Path) -> Dict[str, Any]:
        """Get structure of subfolder."""
        structure = {}
        
        for item in folder.iterdir():
            if item.is_dir():
                structure[item.name] = self._get_subfolder_structure(item)
            else:
                structure[item.name] = "file"
        
        return structure
