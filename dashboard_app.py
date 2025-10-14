# import pickle
# import logging
# import logging.handlers
# import socketserver
# import struct
# import time

# class LogRecordStreamHandler(socketserver.StreamRequestHandler):
#     """
#     Handler that receives pickled LogRecord objects from the CV client.
#     It's specifically designed to interpret the eye-tracking data dictionary
#     and perform real-time analysis and alerting.
#     """
#     def handle(self):
#         """
#         This method is called for each log record received from the client.
#         """
#         try:
#             # Read the length of the incoming log record
#             chunk = self.rfile.read(4)
#             if len(chunk) < 4:
#                 return
#             slen = struct.unpack('>L', chunk)[0]
            
#             # Read the pickled LogRecord object
#             chunk = self.rfile.read(slen)
#             if len(chunk) < slen:
#                 return

#             # Unpickle into a standard LogRecord
#             obj = pickle.loads(chunk)
#             record = logging.makeLogRecord(obj)

#             # --- REAL-TIME ANALYSIS AND CONSOLE OUTPUT ---

#             # Check for high-priority alerts first
#             if getattr(record, 'violation_detected', False):
#                 self.server.total_violations += 1
                
#                 # Determine the alert level (standard violation or cheating)
#                 is_cheat = getattr(record, 'cheat_detected', False)
#                 alert_type = "CHEAT DETECTED" if is_cheat else "VIOLATION"
                
#                 # 
#                 # Print a high-visibility, formatted alert to the console
#                 print("\n" + "!"*60)
#                 print(f"🚨 ALERT from {record.name} | {alert_type} #{self.server.total_violations} 🚨")
#                 print(f"   Timestamp: {getattr(record, 'timestamp_ms', 'N/A')}")
#                 print(f"   Reason: Gaze direction is '{getattr(record, 'gaze_direction', 'N/A')}'")
#                 print(f"   Confidence: {getattr(record, 'gaze_confidence', 0.0):.2f}")
#                 print(f"   Suspicious Moves: {getattr(record, 'suspicious_movements', 0)}")
#                 print("!"*60 + "\n")

#             elif record.levelno >= logging.INFO and record.msg == "Eye tracking script has started.":
#                  print(f"\n✅ CONNECTION ESTABLISHED from: {record.name} at {time.strftime('%H:%M:%S')}\n")

#             else:
#                 # For normal, non-violating logs, just print a clean, single-line summary
#                 # The getattr() function safely retrieves attributes, providing a default value if one doesn't exist.
#                 pitch = getattr(record, 'pitch', 0.0)
#                 yaw = getattr(record, 'yaw', 0.0)
#                 roll = getattr(record, 'roll', 0.0)
#                 velocity = getattr(record, 'eye_velocity', 0.0)

#                 print(
#                     f"OK | {record.name} | "
#                     f"Gaze: {getattr(record, 'gaze_direction', '...')} | "
#                     f"Pose (P/Y/R): {pitch:+.1f}, {yaw:+.1f}, {roll:+.1f} | "
#                     f"Blinks: {getattr(record, 'total_blinks', 0)} | "
#                     f"Velocity: {velocity:.2f}"
#                 )

#         except (EOFError, pickle.UnpicklingError):
#             # This can happen if a client disconnects abruptly.
#             print(f"Client disconnected or sent malformed data.")
#         except Exception as e:
#             print(f"An unexpected server error occurred: {e}")

# class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
#     """
#     A simple multi-threaded TCP socket server for receiving log records.
#     It holds stateful information, such as the total violation count.
#     """
#     allow_reuse_address = True
#     total_violations = 0 # This state is held by the server instance

#     def __init__(self, host='localhost', port=9020, handler=LogRecordStreamHandler):
#         super().__init__((host, port), handler)

# def main():
#     """
#     Sets up and runs the logging server indefinitely.
#     """
#     print("="*60)
#     print("   Central Eye-Tracking Log and Proctoring Alert Server")
#     print("="*60)
#     print(f"Server starting on localhost:9020 at {time.strftime('%Y-%m-%d %H:%M:%S')}")
#     print("Waiting for connection from CV scripts...")
    
#     try:
#         server = LogRecordSocketReceiver()
#         server.serve_forever()
#     except KeyboardInterrupt:
#         # Handle a clean shutdown on Ctrl+C
#         print("\n\n----------------------------------------------------")
#         print("Shutdown signal received.")
#         print(f"Total violations detected during this session: {server.total_violations}")
#         print("Server is closing.")
#         print("----------------------------------------------------")
#         server.shutdown()
#     except Exception as e:
#         print(f"Could not start server. Is the port already in use? Error: {e}")


# if __name__ == '__main__':
#     main()


import streamlit as st
import threading
import queue
import subprocess
import socketserver
import pickle
import struct
import logging
import logging.handlers
import time
import sys
import os

# --- Configuration ---
FACE_TRACKING_HOST, FACE_TRACKING_PORT = "127.0.0.1", 9020
OBJECT_DETECTION_HOST, OBJECT_DETECTION_PORT = "127.0.0.1", 9021
# Script names
FACE_TRACKING_SCRIPT = "main.py"
OBJECT_DETECTION_SCRIPT = "yolo_detection.py" 

# --- 1. THE BACKGROUND LOGGING SERVER ---
# This part of the code runs in a separate thread to listen for logs.

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler that receives pickled LogRecord objects and puts them into a queue."""
    def handle(self):
        try:
            chunk = self.rfile.read(4)
            if len(chunk) < 4: return
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.rfile.read(slen)
            if len(chunk) < slen: return # Prevent unpickling incomplete data

            obj = pickle.loads(chunk)
            record = logging.makeLogRecord(obj)
            
            self.server.log_queue.put(record)
        except (EOFError, ConnectionResetError, struct.error, pickle.UnpicklingError):
            # These errors happen when the client disconnects, which is normal.
            pass
        except Exception as e:
            # For debugging other potential server errors
            print(f"Server thread error: {e}")

class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """A multi-threaded TCP socket server that uses a queue to communicate."""
    allow_reuse_address = True
    def __init__(self, host, port, log_queue, server_type="face_tracking"):
        super().__init__((host, port), LogRecordStreamHandler)
        self.log_queue = log_queue
        self.server_type = server_type

def start_face_tracking_server(q):
    """Function to run the face tracking logging server in its own thread."""
    try:
        server = LogRecordSocketReceiver(FACE_TRACKING_HOST, FACE_TRACKING_PORT, q, "face_tracking")
        server.serve_forever()
    except Exception as e:
        print(f"Could not start face tracking log server: {e}")

def start_object_detection_server(q):
    """Function to run the object detection logging server in its own thread."""
    try:
        server = LogRecordSocketReceiver(OBJECT_DETECTION_HOST, OBJECT_DETECTION_PORT, q, "object_detection")
        server.serve_forever()
    except Exception as e:
        print(f"Could not start object detection log server: {e}")

# --- 2. STREAMLIT UI AND APPLICATION LOGIC ---

st.set_page_config(layout="wide", page_title="Proctoring Dashboard")

# Initialize session state variables
if 'face_tracking_process' not in st.session_state:
    st.session_state.face_tracking_process = None
    st.session_state.object_detection_process = None
    st.session_state.face_tracking_queue = None
    st.session_state.object_detection_queue = None
    st.session_state.face_log_server_thread = None
    st.session_state.object_log_server_thread = None
    st.session_state.last_face_log = None
    st.session_state.last_object_log = None
    st.session_state.face_log_history = []
    st.session_state.object_log_history = []
    st.session_state.combined_log_history = []
    st.session_state.status = "Not Running"
    st.session_state.face_violation_count = 0
    st.session_state.object_violation_count = 0
    st.session_state.total_violation_count = 0
    st.session_state.suspicion_level = 0
    st.session_state.current_prohibited_objects = []
    st.session_state.error_message = ""

# --- UI Layout ---

st.title("👨‍🏫 Real-Time Proctoring Dashboard")
st.markdown("This dashboard monitors the eye-tracking script in real-time and provides status updates for invigilators.")

col1, col2 = st.columns([1, 4])

with col1:
    if st.session_state.face_tracking_process is None:
        if st.button("🚀 Start Monitoring Session", type="primary"):
            # Check if both scripts exist
            if not os.path.exists(FACE_TRACKING_SCRIPT):
                st.error(f"Error: '{FACE_TRACKING_SCRIPT}' not found. Make sure it's in the same directory.")
                st.stop()
            
            if not os.path.exists(OBJECT_DETECTION_SCRIPT):
                st.error(f"Error: '{OBJECT_DETECTION_SCRIPT}' not found. Make sure it's in the same directory.")
                st.stop()

            # Start both log servers
            st.session_state.face_tracking_queue = queue.Queue()
            st.session_state.object_detection_queue = queue.Queue()
            
            st.session_state.face_log_server_thread = threading.Thread(
                target=start_face_tracking_server, args=(st.session_state.face_tracking_queue,), daemon=True
            )
            st.session_state.object_log_server_thread = threading.Thread(
                target=start_object_detection_server, args=(st.session_state.object_detection_queue,), daemon=True
            )
            
            st.session_state.face_log_server_thread.start()
            st.session_state.object_log_server_thread.start()
            time.sleep(1.5)  # Give servers time to bind and listen

            # Launch both processes
            # Face tracking process
            st.session_state.face_tracking_process = subprocess.Popen(
                [sys.executable, FACE_TRACKING_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(__file__) or None
            )
            
            # Object detection process
            st.session_state.object_detection_process = subprocess.Popen(
                [sys.executable, OBJECT_DETECTION_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(__file__) or None
            )
            
            # Setup output queues for both processes
            st.session_state.face_stdout_queue = queue.Queue()
            st.session_state.face_stderr_queue = queue.Queue()
            st.session_state.object_stdout_queue = queue.Queue()
            st.session_state.object_stderr_queue = queue.Queue()
            
            def _reader(stream, q):
                try:
                    for line in iter(stream.readline, ''):
                        if not line:
                            break
                        q.put(line.rstrip('\n'))
                except Exception as e:
                    q.put(f"[stream read error] {e}")
                finally:
                    try:
                        stream.close()
                    except Exception:
                        pass
            
            # Start reader threads for both processes
            threading.Thread(target=_reader, args=(st.session_state.face_tracking_process.stdout, st.session_state.face_stdout_queue), daemon=True).start()
            threading.Thread(target=_reader, args=(st.session_state.face_tracking_process.stderr, st.session_state.face_stderr_queue), daemon=True).start()
            threading.Thread(target=_reader, args=(st.session_state.object_detection_process.stdout, st.session_state.object_stdout_queue), daemon=True).start()
            threading.Thread(target=_reader, args=(st.session_state.object_detection_process.stderr, st.session_state.object_stderr_queue), daemon=True).start()
            
            st.session_state.status = "Connecting..."
            st.session_state.error_message = ""
            st.success("Starting both face tracking and object detection...")
            st.rerun()
    else:
        if st.button("🛑 Stop Monitoring Session"):
            # Stop both processes
            if st.session_state.face_tracking_process:
                st.session_state.face_tracking_process.terminate()
                st.session_state.face_tracking_process = None
            
            if st.session_state.object_detection_process:
                st.session_state.object_detection_process.terminate()
                st.session_state.object_detection_process = None
            
            st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - Session stopped manually.")
            st.info("Monitoring session stopped.")
            st.session_state.status = "Not Running"
            time.sleep(1)
            st.rerun()

status_placeholder = st.empty()
log_placeholder = st.empty()

# --- Main Loop to Process Logs and Update UI ---
if st.session_state.face_tracking_process is not None or st.session_state.object_detection_process is not None:
    # Check if processes have terminated
    face_running = st.session_state.face_tracking_process and st.session_state.face_tracking_process.poll() is None
    object_running = st.session_state.object_detection_process and st.session_state.object_detection_process.poll() is None
    
    if not face_running and st.session_state.face_tracking_process:
        st.error("Face tracking script has terminated unexpectedly.")
        st.session_state.face_tracking_process = None
        st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - ❌ Face tracking terminated")
    
    if not object_running and st.session_state.object_detection_process:
        st.error("Object detection script has terminated unexpectedly.")
        st.session_state.object_detection_process = None
        st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - ❌ Object detection terminated")
    
    # Update overall status
    if not face_running and not object_running:
        st.session_state.status = "Error"
    
    # Process face tracking logs
    while not st.session_state.face_tracking_queue.empty():
        record = st.session_state.face_tracking_queue.get_nowait()
        if st.session_state.last_face_log is None:
            st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - ✅ Connected to face tracking stream")
        st.session_state.last_face_log = record
        
        # Process face tracking violation
        flagged = bool(getattr(record, 'flagged', False)) or (
            float(getattr(record, 'violation_duration', 0.0)) >= 10.0
        )
        violation_detected = bool(getattr(record, 'violation_detected', False))
        gaze_dir = getattr(record, 'gaze_direction', 'within_screen')

        if flagged:
            st.session_state.face_violation_count = getattr(record, 'violation_count', 0)
            dur = float(getattr(record, 'violation_duration', 0.0))
            event = f"🔴 FACE VIOLATION: {gaze_dir} for {dur:.1f}s (#{st.session_state.face_violation_count})"
            st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - {event}")
        elif violation_detected:
            dur = float(getattr(record, 'violation_duration', 0.0))
            event = f"� FACE SUSPICIOUS: {gaze_dir} ({dur:.1f}s)"
            st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - {event}")
    
    # Process object detection logs
    while not st.session_state.object_detection_queue.empty():
        record = st.session_state.object_detection_queue.get_nowait()
        if st.session_state.last_object_log is None:
            st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - ✅ Connected to object detection stream")
        st.session_state.last_object_log = record
        
        # Process object detection violation
        object_violation = bool(getattr(record, 'violation_triggered', False))
        new_violation = bool(getattr(record, 'new_violation', False))
        prohibited_objects = getattr(record, 'prohibited_objects', [])
        st.session_state.current_prohibited_objects = prohibited_objects

        if new_violation:
            st.session_state.object_violation_count = getattr(record, 'violation_count', 0)
            dur = float(getattr(record, 'violation_duration', 0.0))
            objects_str = ', '.join(prohibited_objects)
            event = f"� OBJECT VIOLATION: {objects_str} detected for {dur:.1f}s (#{st.session_state.object_violation_count})"
            st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - {event}")
        elif getattr(record, 'object_violation', False):
            dur = float(getattr(record, 'violation_duration', 0.0))
            objects_str = ', '.join(prohibited_objects)
            event = f"🟠 OBJECT DETECTED: {objects_str} ({dur:.1f}s)"
            st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - {event}")
    
    # Update combined status
    face_flagged = st.session_state.last_face_log and bool(getattr(st.session_state.last_face_log, 'flagged', False))
    object_flagged = st.session_state.last_object_log and bool(getattr(st.session_state.last_object_log, 'violation_triggered', False))
    face_suspicious = st.session_state.last_face_log and bool(getattr(st.session_state.last_face_log, 'violation_detected', False))
    object_suspicious = st.session_state.last_object_log and bool(getattr(st.session_state.last_object_log, 'object_violation', False))
    
    # Calculate total violations
    st.session_state.total_violation_count = st.session_state.face_violation_count + st.session_state.object_violation_count
    
    # Determine overall status
    if face_flagged and object_flagged:
        st.session_state.status = "CRITICAL - Face + Object Violations"
    elif face_flagged:
        st.session_state.status = "FLAGGED - Gaze Violation"
    elif object_flagged:
        st.session_state.status = "FLAGGED - Prohibited Objects"
    elif face_suspicious and object_suspicious:
        st.session_state.status = "SUSPICIOUS - Multiple Issues"
    elif face_suspicious:
        st.session_state.status = "SUSPICIOUS - Gaze Issue"
    elif object_suspicious:
        st.session_state.status = "SUSPICIOUS - Object Detected"
    elif (face_running or object_running):
        st.session_state.status = "Normal"

# Drain stdout/stderr lines from both processes
if st.session_state.get('face_stdout_queue') is not None:
    drained = 0
    while not st.session_state.face_stdout_queue.empty() and drained < 25:
        drained += 1
        line = st.session_state.face_stdout_queue.get_nowait()
        st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - [FACE] {line}")
        # Update status for face tracking
        if (
            st.session_state.status in ["Connecting...", "Connecting"]
            and (
                "Camera warm-up complete" in line
                or "Eye tracking update" in line
                or "Camera source" in line
            )
        ):
            st.session_state.status = "Normal"

if st.session_state.get('object_stdout_queue') is not None:
    drained = 0
    while not st.session_state.object_stdout_queue.empty() and drained < 25:
        drained += 1
        line = st.session_state.object_stdout_queue.get_nowait()
        st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - [OBJECT] {line}")
        # Update status for object detection
        if (
            st.session_state.status in ["Connecting...", "Connecting"]
            and (
                "YOLO object detection started" in line
                or "Starting object detection" in line
            )
        ):
            st.session_state.status = "Normal"

if st.session_state.get('face_stderr_queue') is not None:
    drained = 0
    while not st.session_state.face_stderr_queue.empty() and drained < 25:
        drained += 1
        line = st.session_state.face_stderr_queue.get_nowait()
        st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - [FACE ERROR] {line}")

if st.session_state.get('object_stderr_queue') is not None:
    drained = 0
    while not st.session_state.object_stderr_queue.empty() and drained < 25:
        drained += 1
        line = st.session_state.object_stderr_queue.get_nowait()
        st.session_state.combined_log_history.insert(0, f"{time.strftime('%H:%M:%S')} - [OBJECT ERROR] {line}")

# --- Display Logic ---
status_styles = """
    <style>
    .status-box { border-radius: 10px; padding: 25px; text-align: center; color: white; font-size: 24px; font-weight: bold; }
    .normal { background-color: #28a745; }
    .suspicious { background-color: #ffc107; color: black; }
    .flagged { background-color: #dc3545; }
    .not-running { background-color: #6c757d; }
    .error { background-color: #a40000; }
    .connecting { background-color: #007bff; }
    </style>
"""
st.markdown(status_styles, unsafe_allow_html=True)

with status_placeholder.container():
    # Map status text to CSS class names
    status_text = st.session_state.status
    status_map = {
        "Not Running": "not-running",
        "Connecting...": "connecting",
        "Connecting": "connecting",
        "Normal": "normal",
        "Suspicious": "suspicious",
        "Flagged": "flagged",
        "Error": "error",
    }
    status_class = status_map.get(status_text, status_text.lower().replace(' ', '-'))
    st.markdown(
        f'<div class="status-box {status_class}">STATUS: {status_text.upper()}</div>',
        unsafe_allow_html=True
    )
    
    st.header("Live Metrics")
    if (st.session_state.last_face_log or st.session_state.last_object_log) and st.session_state.status != "Error":
        # Face tracking metrics
        face_rec = st.session_state.last_face_log
        object_rec = st.session_state.last_object_log
        
        # Create two rows of metrics
        c1, c2, c3, c4 = st.columns(4)
        
        # Top row - Face tracking metrics
        if face_rec:
            c1.metric("Gaze Direction", getattr(face_rec, 'gaze_direction', 'N/A'))
            c2.metric("Face Violations", st.session_state.face_violation_count)
            c3.metric("Head Pose (Yaw)", f"{getattr(face_rec, 'yaw', 0.0):.1f}°")
            c4.metric("Eye Velocity", f"{getattr(face_rec, 'eye_velocity', 0.0):.2f}")
        else:
            c1.metric("Gaze Direction", "Connecting...")
            c2.metric("Face Violations", 0)
            c3.metric("Head Pose (Yaw)", "N/A")
            c4.metric("Eye Velocity", "N/A")
        
        # Bottom row - Object detection metrics
        c5, c6, c7, c8 = st.columns(4)
        
        if object_rec:
            detected_objs = getattr(object_rec, 'detected_objects', [])
            prohibited_objs = getattr(object_rec, 'prohibited_objects', [])
            c5.metric("Detected Objects", f"{len(detected_objs)} items")
            c6.metric("Object Violations", st.session_state.object_violation_count)
            c7.metric("Prohibited Items", ', '.join(prohibited_objs) if prohibited_objs else 'None')
            c8.metric("Detection Time", f"{getattr(object_rec, 'inference_time', 0.0):.1f}ms")
        else:
            c5.metric("Detected Objects", "Connecting...")
            c6.metric("Object Violations", 0)
            c7.metric("Prohibited Items", "N/A")
            c8.metric("Detection Time", "N/A")
        
        # Combined metrics
        st.subheader("Combined Status")
        col_combined1, col_combined2 = st.columns(2)
        col_combined1.metric("Total Violations", st.session_state.total_violation_count)
        
        # Show current prohibited objects if any
        if st.session_state.current_prohibited_objects:
            objects_str = ', '.join(st.session_state.current_prohibited_objects)
            col_combined2.metric("⚠️ Current Threats", objects_str, delta="ALERT")
        else:
            col_combined2.metric("✅ Current Status", "All Clear", delta="SAFE")
            
    elif st.session_state.status not in ["Not Running", "Error"]:
        st.info("Waiting for data from face tracking and object detection systems...")
        # Simple timeout hint if no data for >5s
        if 'connect_start' not in st.session_state:
            st.session_state.connect_start = time.time()
        elif time.time() - st.session_state.connect_start > 8 and not st.session_state.last_face_log and not st.session_state.last_object_log:
            st.warning("No data yet. Ensure both scripts can access cameras and firewall allows connections.")

with log_placeholder.container():
    st.header("Event Log")
    if len(st.session_state.combined_log_history) > 30:
        st.session_state.combined_log_history = st.session_state.combined_log_history[:30]
    log_text = "\n".join(st.session_state.combined_log_history)
    st.text_area("Combined Logs (Face Tracking + Object Detection)", value=log_text, height=300, disabled=True)

if st.session_state.face_tracking_process or st.session_state.object_detection_process:
    time.sleep(0.5)
    st.rerun()

