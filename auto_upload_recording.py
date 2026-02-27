#!/usr/bin/env python3
"""
Auto-upload Zoom recordings to S3
Run this script to monitor your Zoom folder and automatically upload new recordings
"""
import sys
import os
import time
import boto3
import uuid
from pathlib import Path
from datetime import datetime

s3_client = boto3.client('s3')

ZOOM_RECORDING_DIR = Path.home() / "Documents" / "Zoom"
S3_BUCKET = "meeting-audio-069908900405"

def upload_recording(file_path, meeting_id=None):
    """Upload a single recording to S3"""
    if meeting_id is None:
        meeting_id = f"auto-{uuid.uuid4().hex[:8]}"
    
    file_key = f"recordings/{meeting_id}/{os.path.basename(file_path)}"
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Uploading: {os.path.basename(file_path)}")
    
    try:
        s3_client.upload_file(file_path, S3_BUCKET, file_key)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Uploaded! Meeting ID: {meeting_id}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing will start automatically.")
        return meeting_id
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Upload failed: {str(e)}")
        return None

def get_existing_recordings():
    """Get list of already processed recordings (by file, not folder)"""
    processed = set()
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix='recordings/')
        if 'Contents' in response:
            for obj in response['Contents']:
                # Store the full key to track individual files
                processed.add(obj['Key'])
    except Exception as e:
        print(f"Warning: Could not list S3 objects: {e}")
    return processed

def monitor_zoom_folder():
    """Monitor Zoom folder for new recordings"""
    print("=" * 60)
    print("🎙️  Auto-Zoom-Uploader")
    print("=" * 60)
    print()
    print(f"Monitoring: {ZOOM_RECORDING_DIR}")
    print(f"Target: {S3_BUCKET}")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    processed_meetings = get_existing_recordings()
    
    while True:
        try:
            if not ZOOM_RECORDING_DIR.exists():
                print(f"Zoom folder not found at {ZOOM_RECORDING_DIR}")
                time.sleep(5)
                continue
            
            # Find all meeting folders
            meeting_folders = [d for d in ZOOM_RECORDING_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
            
            if meeting_folders:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(meeting_folders)} meeting folder(s)")
            
            for folder in meeting_folders:
                meeting_id = folder.name
                
                # Find video files in folder
                video_files = list(folder.glob("*.mp4")) + list(folder.glob("*.mov")) + list(folder.glob("*.m4v"))
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking {meeting_id}: found {len(video_files)} video file(s)")
                
                if video_files:
                    video_file = video_files[0]
                    file_key = f"recordings/{meeting_id}/{os.path.basename(str(video_file))}"
                    
                    # Skip if this specific file was already uploaded
                    if file_key in processed_meetings:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Already uploaded: {file_key}")
                        continue
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Found video in {meeting_id}")
                    result = upload_recording(str(video_file), meeting_id)
                    if result:
                        processed_meetings.add(file_key)
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No video files in {meeting_id}")
            
            time.sleep(10)  # Check every 10 seconds
            
        except KeyboardInterrupt:
            print("\n\n👋 Stopping auto-uploader...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    import sys
    print("Starting auto-uploader...")
    
    # Check if --reset flag is passed to clear processed recordings
    if "--reset" in sys.argv:
        print("🔄 Resetting processed recordings...")
        try:
            response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix='recordings/')
            if 'Contents' in response:
                print(f"Found {len(response['Contents'])} existing recordings in S3")
            else:
                print("No existing recordings in S3")
        except Exception as e:
            print(f"Error checking S3: {e}")
    
    monitor_zoom_folder()
