#!/usr/bin/env python3
"""
Example script demonstrating how to use the Train Video Processing System.
This script shows how to process videos programmatically with custom settings.
"""

import os
from pathlib import Path
from main import TrainVideoProcessor

def run_example():
    """Run an example of the train video processing system."""
    
    # Configuration
    INPUT_DIR = "input_videos"
    OUTPUT_DIR = "Processed_Video"
    
    print("🚂 Train Video Processing System - Example")
    print("=" * 50)
    
    # Check if input directory exists
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Input directory '{INPUT_DIR}' not found!")
        print(f"Please create the directory and add your train videos.")
        print(f"Supported formats: MP4, AVI, MOV")
        return
    
    # Check if there are any videos
    video_files = list(Path(INPUT_DIR).glob("*.mp4")) + \
                  list(Path(INPUT_DIR).glob("*.avi")) + \
                  list(Path(INPUT_DIR).glob("*.mov"))
    
    if not video_files:
        print(f"❌ No video files found in '{INPUT_DIR}'")
        print(f"Please add train videos to the input directory.")
        return
    
    print(f"📁 Found {len(video_files)} video(s) to process:")
    for video in video_files:
        print(f"   - {video.name}")
    
    print(f"\n🎯 Processing videos...")
    print(f"📤 Output will be saved to: {OUTPUT_DIR}")
    
    # Initialize processor
    processor = TrainVideoProcessor(INPUT_DIR, OUTPUT_DIR)
    
    try:
        # Process all videos
        results = processor.process_all_videos()
        
        print(f"\n✅ Processing complete!")
        print(f"📊 Results:")
        print(f"   - Videos processed: {len(results)}")
        
        total_coaches = sum(len(data.get('coaches', [])) for data in results.values())
        print(f"   - Total coaches: {total_coaches}")
        
        # Show per-train summary
        for train_number, train_data in results.items():
            coaches = train_data.get('coaches', [])
            print(f"   - Train {train_number}: {len(coaches)} coaches")
        
        print(f"\n📄 Report generated: {OUTPUT_DIR}/Final_Report.pdf")
        print(f"📁 Processed data: {OUTPUT_DIR}/")
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        print(f"Please check the logs for more details.")

if __name__ == "__main__":
    run_example()
