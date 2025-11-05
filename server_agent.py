#!/usr/bin/env python3
"""
CheatGuard Server Agent - Runs on Student's PC
This script runs on the exam machine and accepts commands from the proctor's dashboard
to start/stop detection scripts and stream logs back.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import sys
import os
import threading
import queue
import socket
import pickle
import struct
import logging
import logging.handlers
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from proctor's PC

# Global state
class SystemState:
    def __init__(self):
        self.face_tracking_process = None
        self.object_detection_process = None
        self.face_log_queue = queue.Queue()
        self.object_log_queue = queue.Queue()
        self.face_log_server = None
        self.object_log_server = None
        self.status = "Idle"
        self.face_violations = 0
        self.object_violations = 0
        self.last_face_log = None
        self.last_object_log = None
        self.recent_events = []
        self.server_ip = self.get_local_ip()
        
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

state = SystemState()

# ============================================================================
# LOG RECEIVING SERVERS (Same as dashboard_app.py)
# ============================================================================

class LogRecordStreamHandler:
    """Handler for receiving logs from detection scripts"""
    pass

import socketserver

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            chunk = self.rfile.read(4)
            if len(chunk) < 4: return
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.rfile.read(slen)
            if len(chunk) < slen: return
            
            obj = pickle.loads(chunk)
            record = logging.makeLogRecord(obj)
            
            # Put log in appropriate queue based on server type
            if self.server.server_type == "face":
                state.face_log_queue.put(record)
            else:
                state.object_log_queue.put(record)
                
        except Exception as e:
            pass

class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    def __init__(self, host, port, server_type):
        super().__init__((host, port), LogRecordStreamHandler)
        self.server_type = server_type

def start_log_servers():
    """Start both log receiving servers"""
    def run_face_server():
        state.face_log_server = LogRecordSocketReceiver("0.0.0.0", 9020, "face")
        state.face_log_server.serve_forever()
    
    def run_object_server():
        state.object_log_server = LogRecordSocketReceiver("0.0.0.0", 9021, "object")
        state.object_log_server.serve_forever()
    
    threading.Thread(target=run_face_server, daemon=True).start()
    threading.Thread(target=run_object_server, daemon=True).start()
    time.sleep(1)
    print("✅ Log servers started on ports 9020 and 9021")

def process_logs():
    """Background thread to process incoming logs"""
    while True:
        try:
            # Process face tracking logs
            while not state.face_log_queue.empty():
                record = state.face_log_queue.get_nowait()
                state.last_face_log = record
                
                # Check for violations
                flagged = bool(getattr(record, 'flagged', False))
                if flagged:
                    state.face_violations = getattr(record, 'violation_count', 0)
                    gaze_dir = getattr(record, 'gaze_direction', 'unknown')
                    dur = float(getattr(record, 'violation_duration', 0.0))
                    event = {
                        'timestamp': time.strftime('%H:%M:%S'),
                        'type': 'face_violation',
                        'message': f"🔴 Face Violation: {gaze_dir} for {dur:.1f}s",
                        'severity': 'high'
                    }
                    state.recent_events.insert(0, event)
                    if len(state.recent_events) > 50:
                        state.recent_events = state.recent_events[:50]
            
            # Process object detection logs
            while not state.object_log_queue.empty():
                record = state.object_log_queue.get_nowait()
                state.last_object_log = record
                
                # Check for violations
                new_violation = bool(getattr(record, 'new_violation', False))
                if new_violation:
                    state.object_violations = getattr(record, 'violation_count', 0)
                    prohibited = getattr(record, 'prohibited_objects', [])
                    dur = float(getattr(record, 'violation_duration', 0.0))
                    event = {
                        'timestamp': time.strftime('%H:%M:%S'),
                        'type': 'object_violation',
                        'message': f"🚨 Object Violation: {', '.join(prohibited)} for {dur:.1f}s",
                        'severity': 'high'
                    }
                    state.recent_events.insert(0, event)
                    if len(state.recent_events) > 50:
                        state.recent_events = state.recent_events[:50]
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error processing logs: {e}")
            time.sleep(1)

# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system status"""
    face_running = state.face_tracking_process and state.face_tracking_process.poll() is None
    object_running = state.object_detection_process and state.object_detection_process.poll() is None
    
    # Determine overall status
    if face_running and object_running:
        status = "Running"
    elif face_running or object_running:
        status = "Partial"
    else:
        status = "Idle"
    
    # Get latest data
    response = {
        'status': status,
        'face_tracking_running': face_running,
        'object_detection_running': object_running,
        'face_violations': state.face_violations,
        'object_violations': state.object_violations,
        'total_violations': state.face_violations + state.object_violations,
        'recent_events': state.recent_events[:20],
        'timestamp': datetime.now().isoformat()
    }
    
    # Add face tracking data if available
    if state.last_face_log:
        response['face_data'] = {
            'gaze_direction': getattr(state.last_face_log, 'gaze_direction', 'N/A'),
            'head_yaw': getattr(state.last_face_log, 'yaw', 0.0),
            'eye_velocity': getattr(state.last_face_log, 'eye_velocity', 0.0),
            'flagged': bool(getattr(state.last_face_log, 'flagged', False))
        }
    
    # Add object detection data if available
    if state.last_object_log:
        response['object_data'] = {
            'detected_objects': getattr(state.last_object_log, 'detected_objects', []),
            'prohibited_objects': getattr(state.last_object_log, 'prohibited_objects', []),
            'inference_time': getattr(state.last_object_log, 'inference_time', 0.0),
            'violation_active': bool(getattr(state.last_object_log, 'object_violation', False))
        }
    
    return jsonify(response)

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start both detection scripts"""
    try:
        # Check if already running
        if state.face_tracking_process or state.object_detection_process:
            return jsonify({'success': False, 'message': 'System already running'}), 400
        
        # Check if scripts exist
        if not os.path.exists('main.py'):
            return jsonify({'success': False, 'message': 'main.py not found'}), 404
        if not os.path.exists('yolo_detection.py'):
            return jsonify({'success': False, 'message': 'yolo_detection.py not found'}), 404
        
        # Start face tracking
        state.face_tracking_process = subprocess.Popen(
            [sys.executable, 'main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        time.sleep(2)
        
        # Start object detection
        state.object_detection_process = subprocess.Popen(
            [sys.executable, 'yolo_detection.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        state.status = "Running"
        event = {
            'timestamp': time.strftime('%H:%M:%S'),
            'type': 'system',
            'message': '✅ Monitoring session started',
            'severity': 'info'
        }
        state.recent_events.insert(0, event)
        
        return jsonify({'success': True, 'message': 'Monitoring started successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop both detection scripts"""
    try:
        # Stop face tracking
        if state.face_tracking_process:
            state.face_tracking_process.terminate()
            state.face_tracking_process.wait(timeout=5)
            state.face_tracking_process = None
        
        # Stop object detection
        if state.object_detection_process:
            state.object_detection_process.terminate()
            state.object_detection_process.wait(timeout=5)
            state.object_detection_process = None
        
        state.status = "Idle"
        event = {
            'timestamp': time.strftime('%H:%M:%S'),
            'type': 'system',
            'message': '🛑 Monitoring session stopped',
            'severity': 'info'
        }
        state.recent_events.insert(0, event)
        
        return jsonify({'success': True, 'message': 'Monitoring stopped successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/info', methods=['GET'])
def get_info():
    """Get server information"""
    return jsonify({
        'server_ip': state.server_ip,
        'server_port': 5000,
        'face_log_port': 9020,
        'object_log_port': 9021,
        'version': '1.0.0',
        'status': state.status
    })

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("🛡️  CHEATGUARD SERVER AGENT")
    print("=" * 70)
    print(f"🖥️  Server IP: {state.server_ip}")
    print(f"🔌 API Port: 5000")
    print(f"🔌 Face Log Port: 9020")
    print(f"🔌 Object Log Port: 9021")
    print("=" * 70)
    print(f"\n📊 PROCTOR'S DASHBOARD CONNECTION:")
    print(f"   Use this IP in the proctor's dashboard: {state.server_ip}")
    print("=" * 70)
    print("\nStarting services...")
    
    # Start log servers
    start_log_servers()
    
    # Start log processing thread
    threading.Thread(target=process_logs, daemon=True).start()
    
    print("\n✅ Server agent ready!")
    print(f"🌐 API available at: http://{state.server_ip}:5000")
    print("\nWaiting for commands from proctor's dashboard...\n")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()
