#!/usr/bin/env python3
"""
YOLO Object Detection Module for Proctoring System

This module runs YOLO object detection and sends structured logs to the dashboard
for real-time monitoring of prohibited objects during exams/proctoring.

Prohibited Objects: Chit, Phone, Earbuds
Violation Logic: Objects must be detected continuously for 3-4 seconds to trigger violation
"""

import cv2
import time
import csv
import json
import logging
import logging.handlers
import sys
import os
import threading
import re
import subprocess
import requests
import numpy as np
from datetime import datetime
from queue import Queue, Empty as QueueEmpty

# Import configuration from config.py
try:
    from config import (
        OBJECT_DETECTION_USE_IP_WEBCAM as USE_IP_WEBCAM,
        OBJECT_DETECTION_IP_WEBCAM_URL as IP_WEBCAM_URL,
        OBJECT_DETECTION_CAMERA_SOURCE as CAMERA_SOURCE,
        YOLO_CONFIDENCE_THRESHOLD as CONFIDENCE_THRESHOLD,
        OBJECT_VIOLATION_DURATION as VIOLATION_DURATION,
        PROHIBITED_OBJECTS,
        LOG_FOLDER,
        OBJECT_DETECTION_SOCKET_HOST as SOCKET_HOST,
        OBJECT_DETECTION_SOCKET_PORT as SOCKET_PORT
    )
except ImportError:
    # Fallback configuration if config.py not available
    USE_IP_WEBCAM = False  # Using CAMO - phone appears as Camera 1
    IP_WEBCAM_URL = ""  # Not needed with CAMO
    CAMERA_SOURCE = 1  # Desk-facing camera (phone via CAMO USB)
    CONFIDENCE_THRESHOLD = 0.3
    VIOLATION_DURATION = 3.0
    PROHIBITED_OBJECTS = ['Chit', 'Phone', 'Earbuds']
    LOG_FOLDER = "logs"
    SOCKET_HOST = "127.0.0.1"
    SOCKET_PORT = 9021

# Global state variables
current_prohibited = []
violation_start_time = None
violation_triggered = False
violation_count = 0
detection_active = True
csv_data = []

def get_ip_webcam_frame(url, timeout=5):
    """
    Fetch a frame from IP webcam (phone camera).
    
    Args:
        url: The IP webcam URL
        timeout: Request timeout in seconds
        
    Returns:
        frame: OpenCV frame or None if failed
    """
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            image_array = np.array(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            return frame
        else:
            print(f"Failed to fetch frame: HTTP {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"Timeout fetching frame from {url}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"Connection error to {url}")
        return None
    except Exception as e:
        print(f"Error fetching IP webcam frame: {e}")
        return None


def setup_logging():
    """Configure logging to send to the dashboard server."""
    logger = logging.getLogger('YOLO-ObjectDetection')
    logger.setLevel(logging.DEBUG)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Console handler for terminal output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)s %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Socket handler to send logs to dashboard
        try:
            socket_handler = logging.handlers.SocketHandler(SOCKET_HOST, SOCKET_PORT)
            socket_handler.setLevel(logging.INFO)
            logger.addHandler(socket_handler)
        except Exception:
            # If socket logging fails, continue with console logging only
            pass

        # Disable propagation to prevent duplicate logs
        logger.propagate = False

    return logger

def parse_yolo_output(output_line):
    """
    Parse YOLO output line to extract detection information.
    
    Example input: "0: 480x640 1 Chit, 1 Hand, 1 Phone, 628.5ms"
    Returns: {
        'detected_objects': ['Chit', 'Hand', 'Phone'],
        'object_counts': {'Chit': 1, 'Hand': 1, 'Phone': 1},
        'inference_time': 628.5
    }
    """
    try:
        # Extract the main detection part (between dimensions and timing)
        pattern = r'0: \d+x\d+ (.+?), ([\d.]+)ms'
        match = re.search(pattern, output_line)
        
        if not match:
            return None
            
        detections_str = match.group(1)
        inference_time = float(match.group(2))
        
        # Parse individual detections
        detection_parts = [part.strip() for part in detections_str.split(',')]
        detected_objects = []
        object_counts = {}
        
        for part in detection_parts:
            # Match patterns like "1 Chit", "2 Hands", "1 Phone"
            obj_match = re.match(r'(\d+)\s+(.+)', part)
            if obj_match:
                count = int(obj_match.group(1))
                obj_name = obj_match.group(2)
                
                # Handle plural forms (Hands -> Hand)
                if obj_name.endswith('s') and obj_name != 'Earbuds':
                    obj_name = obj_name[:-1]
                
                detected_objects.extend([obj_name] * count)
                object_counts[obj_name] = count
        
        return {
            'detected_objects': detected_objects,
            'object_counts': object_counts,
            'inference_time': inference_time
        }
        
    except Exception as e:
        print(f"Error parsing YOLO output: {e}")
        return None

def analyze_detections(detection_data):
    """
    Analyze detections for prohibited objects and violation logic.
    
    Args:
        detection_data: Parsed detection information
        
    Returns:
        dict: Analysis results with violation status
    """
    global current_prohibited, violation_start_time, violation_triggered, violation_count
    
    if not detection_data:
        # No detections - reset violation tracking
        current_prohibited = []
        violation_start_time = None
        violation_triggered = False
        return {
            'prohibited_detected': [],
            'violation_active': False,
            'violation_duration': 0.0,
            'violation_triggered': False,
            'new_violation': False
        }
    
    # Find prohibited objects in current detection
    detected_objects = detection_data['detected_objects']
    prohibited_detected = [obj for obj in detected_objects if obj in PROHIBITED_OBJECTS]
    
    current_time = time.time()
    new_violation = False
    
    if prohibited_detected:
        # Check if this is a new detection pattern
        if set(prohibited_detected) != set(current_prohibited):
            # New or changed prohibited objects
            current_prohibited = prohibited_detected.copy()
            violation_start_time = current_time
            violation_triggered = False
            print(f"🔍 Prohibited objects detected: {prohibited_detected}")
        
        # Calculate violation duration
        violation_duration = current_time - violation_start_time if violation_start_time else 0.0
        
        # Check if violation threshold is reached
        if violation_duration >= VIOLATION_DURATION and not violation_triggered:
            violation_triggered = True
            violation_count += 1
            new_violation = True
            print(f"🚨 OBJECT VIOLATION #{violation_count}: {prohibited_detected} detected for {violation_duration:.1f}s!")
        
        return {
            'prohibited_detected': prohibited_detected,
            'violation_active': True,
            'violation_duration': violation_duration,
            'violation_triggered': violation_triggered,
            'new_violation': new_violation
        }
    else:
        # No prohibited objects - reset if we were tracking
        if current_prohibited:
            duration = current_time - violation_start_time if violation_start_time else 0.0
            if duration > 1.0:  # Only log if it was a significant duration
                print(f"✅ Prohibited objects cleared after {duration:.1f}s")
        
        current_prohibited = []
        violation_start_time = None
        violation_triggered = False
        
        return {
            'prohibited_detected': [],
            'violation_active': False,
            'violation_duration': 0.0,
            'violation_triggered': False,
            'new_violation': False
        }

def log_detection_data(detection_data, analysis_result):
    """
    Log detection data to CSV and send to dashboard via socket.
    
    Args:
        detection_data: Parsed YOLO detection data
        analysis_result: Violation analysis results
    """
    global csv_data
    
    timestamp = int(time.time() * 1000)
    
    # Prepare CSV entry
    csv_entry = [
        timestamp,
        json.dumps(detection_data['detected_objects']) if detection_data else "[]",
        json.dumps(analysis_result['prohibited_detected']),
        analysis_result['violation_active'],
        analysis_result['violation_duration'],
        analysis_result['violation_triggered'],
        violation_count,
        detection_data['inference_time'] if detection_data else 0.0,
        len(analysis_result['prohibited_detected'])
    ]
    
    csv_data.append(csv_entry)
    
    # Prepare socket log data
    log_data = {
        "timestamp_ms": timestamp,
        "source": "object_detection",
        "detected_objects": detection_data['detected_objects'] if detection_data else [],
        "prohibited_objects": analysis_result['prohibited_detected'],
        "object_violation": analysis_result['violation_active'],
        "violation_duration": analysis_result['violation_duration'],
        "detection_confidence": CONFIDENCE_THRESHOLD,
        "violation_triggered": analysis_result['violation_triggered'],
        "violation_count": violation_count,
        "inference_time": detection_data['inference_time'] if detection_data else 0.0,
        "new_violation": analysis_result['new_violation']
    }
    
    # Send to dashboard via socket logging
    logger = logging.getLogger('YOLO-ObjectDetection')
    logger.info("Object detection update", extra=log_data)

def save_csv_logs():
    """Save accumulated CSV data to file."""
    global csv_data
    
    if not csv_data:
        return
    
    # Ensure log folder exists
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename = os.path.join(LOG_FOLDER, f"object_detection_log_{timestamp}.csv")
    
    # CSV column headers
    headers = [
        "Timestamp (ms)",
        "Detected Objects",
        "Prohibited Objects", 
        "Violation Active",
        "Violation Duration",
        "Violation Triggered",
        "Total Violations",
        "Inference Time (ms)",
        "Prohibited Count"
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(csv_data)
        
        print(f"💾 Object detection data saved to {filename}")
        csv_data = []  # Clear the data after saving
        
    except Exception as e:
        print(f"❌ Error saving CSV data: {e}")

def run_yolo_detection():
    """
    Main function to run YOLO object detection with real-time monitoring.
    """
    global detection_active
    
    logger = setup_logging()
    logger.info("YOLO object detection started for proctoring system.")
    
    print("🎯 YOLO OBJECT DETECTION FOR PROCTORING")
    print("=" * 50)
    print(f"Camera Source: Camera {CAMERA_SOURCE} (Phone via CAMO USB)")
    print(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
    print(f"Violation Duration: {VIOLATION_DURATION}s")
    print(f"Prohibited Objects: {', '.join(PROHIBITED_OBJECTS)}")
    print(f"Socket: {SOCKET_HOST}:{SOCKET_PORT}")
    print("=" * 50)
    
    try:
        # Check if YOLO custom script exists
        yolo_script = os.path.join("yolo_custom", "yolo_custom.py")
        if not os.path.exists(yolo_script):
            print(f"❌ YOLO script not found: {yolo_script}")
            return
        
        print("🚀 Starting YOLO object detection...")
        print(f"📱 Using Camera {CAMERA_SOURCE} (Phone via CAMO)")
        print("   Make sure CAMO is running and phone is connected via USB")
        print("Press Ctrl+C to stop detection and save logs")
        
        # Set environment variables for the subprocess
        env = os.environ.copy()
        env['USE_IP_WEBCAM'] = str(USE_IP_WEBCAM)
        env['IP_WEBCAM_URL'] = IP_WEBCAM_URL
        
        # Start YOLO process and capture output
        process = subprocess.Popen(
            [sys.executable, yolo_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=os.path.dirname(__file__) or None,
            env=env
        )
        
        # Function to read YOLO output
        def read_output(pipe, queue):
            try:
                for line in iter(pipe.readline, ''):
                    if line:
                        queue.put(line.strip())
            except Exception as e:
                print(f"Error reading output: {e}")
            finally:
                pipe.close()
        
        # Start threads to read stdout
        output_queue = Queue()
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, output_queue))
        stdout_thread.daemon = True
        stdout_thread.start()
        
        # Process YOLO output in real-time
        try:
            while detection_active:
                try:
                    # Get output from YOLO
                    line = output_queue.get(timeout=1.0)
                    
                    # ALWAYS print the raw output for visibility
                    print(f"[YOLO] {line}")
                    
                    # Parse and analyze the detection
                    detection_data = parse_yolo_output(line)
                    if detection_data:  # Only process valid detections
                        analysis_result = analyze_detections(detection_data)
                        
                        # Log the data
                        log_detection_data(detection_data, analysis_result)
                        
                        # Print summary for console
                        objects_str = ', '.join(detection_data['detected_objects'])
                        print(f"Detected: {objects_str} | Prohibited: {', '.join(analysis_result['prohibited_detected']) or 'None'}")
                    
                except QueueEmpty:
                    # Timeout - this is normal, continue
                    continue
                except Exception as e:
                    # Other error - print and continue
                    print(f"Error processing YOLO output: {e}")
                    continue
                    
        except KeyboardInterrupt:
            print("\n🛑 Detection stopped by user")
            detection_active = False
        
        # Cleanup
        process.terminate()
        process.wait()
        
    except Exception as e:
        print(f"❌ Error in YOLO detection: {e}")
        logger.error(f"YOLO detection error: {e}")
    
    finally:
        # Save logs before exit
        save_csv_logs()
        logger.info("YOLO object detection stopped.")
        print("👋 Object detection session ended")

if __name__ == "__main__":
    try:
        run_yolo_detection()
    except KeyboardInterrupt:
        print("\n🛑 Object detection terminated by user")
        save_csv_logs()
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        save_csv_logs()