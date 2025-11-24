#!/usr/bin/env python3
"""
CheatGuard Multi-Student Dashboard - Runs on Proctor's PC
Monitor up to 3 students simultaneously with individual control and status tracking
"""

import streamlit as st
import requests
import time
import json
import os
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Page config
st.set_page_config(
    page_title="CheatGuard - Multi-Student Monitor",
    page_icon="🛡️",
    layout="wide"
)

# File to store student IPs
STUDENT_IPS_FILE = "student_ips.json"

# ============================================================================
# PERSISTENCE FUNCTIONS
# ============================================================================

def save_student_ips(students):
    """Save student IP addresses to JSON file"""
    try:
        ips = {str(student_id): data['ip'] for student_id, data in students.items()}
        with open(STUDENT_IPS_FILE, 'w') as f:
            json.dump(ips, f, indent=2)
    except Exception as e:
        print(f"Error saving student IPs: {e}")

def load_student_ips():
    """Load student IP addresses from JSON file"""
    try:
        if os.path.exists(STUDENT_IPS_FILE):
            with open(STUDENT_IPS_FILE, 'r') as f:
                ips = json.load(f)
                return {int(k): v for k, v in ips.items()}
    except Exception as e:
        print(f"Error loading student IPs: {e}")
    return {1: "", 2: "", 3: ""}

# ============================================================================
# API FUNCTIONS (copied from proctor_dashboard.py)
# ============================================================================

def check_connection(server_ip):
    """Test connection to server agent"""
    try:
        response = requests.get(f"http://{server_ip}:5000/api/info", timeout=3)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except Exception as e:
        return False, str(e)

def get_status(server_ip):
    """Get current system status from server"""
    try:
        response = requests.get(f"http://{server_ip}:5000/api/status", timeout=5)
        if response.status_code == 200:
            return response.json(), None
        return None, f"HTTP {response.status_code}"
    except Exception as e:
        return None, str(e)

def start_monitoring(server_ip):
    """Send command to start monitoring"""
    try:
        response = requests.post(f"http://{server_ip}:5000/api/start", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {'success': False, 'message': f"HTTP {response.status_code}"}
    except Exception as e:
        return {'success': False, 'message': str(e)}

def stop_monitoring(server_ip):
    """Send command to stop monitoring"""
    try:
        response = requests.post(f"http://{server_ip}:5000/api/stop", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {'success': False, 'message': f"HTTP {response.status_code}"}
    except Exception as e:
        return {'success': False, 'message': str(e)}

# ============================================================================
# CONCURRENT POLLING
# ============================================================================

def poll_student_status(student_id, ip):
    """Poll a single student's status (thread-safe)"""
    if not ip:
        return student_id, None, "No IP"
    
    status_data, error = get_status(ip)
    return student_id, status_data, error

def poll_all_students(students):
    """Poll all students concurrently using threading"""
    results = {}
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(poll_student_status, student_id, data['ip']): student_id 
            for student_id, data in students.items() 
            if data.get('connected', False)
        }
        
        for future in as_completed(futures, timeout=6):
            try:
                student_id, status_data, error = future.result(timeout=1)
                results[student_id] = {'status_data': status_data, 'error': error}
            except Exception as e:
                student_id = futures[future]
                results[student_id] = {'status_data': None, 'error': str(e)}
    
    return results

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'students' not in st.session_state:
    # Load saved students
    saved_ips = load_student_ips()
    
    # Start with one student slot
    st.session_state.students = {
        1: {
            'ip': saved_ips.get(1, ""),
            'connected': False,
            'monitoring': False,
            'status_data': None,
            'last_update': None
        }
    }

if 'next_student_id' not in st.session_state:
    st.session_state.next_student_id = 2

if 'max_students' not in st.session_state:
    st.session_state.max_students = 10  # Maximum allowed students

if 'sound_alerts' not in st.session_state:
    st.session_state.sound_alerts = False

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

# ============================================================================
# UI STYLING
# ============================================================================

st.markdown("""
    <style>
    .student-card {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        background-color: white;
    }
    .status-box { 
        border-radius: 10px; 
        padding: 20px; 
        text-align: center; 
        color: white; 
        font-size: 20px; 
        font-weight: bold;
        margin: 10px 0;
    }
    .status-normal { background-color: #28a745; }
    .status-cheating { background-color: #dc3545; }
    .status-disconnected { background-color: #6c757d; }
    .status-idle { background-color: #17a2b8; }
    .metric-box {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        text-align: center;
    }
    .summary-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.title("🛡️ CheatGuard - Multi-Student Monitoring Dashboard")
st.markdown("### Monitor multiple students dynamically")
st.markdown("---")

# ============================================================================
# SIDEBAR - STUDENT SETUP
# ============================================================================

with st.sidebar:
    st.header("🎓 Student Management")
    
    # Add Student Button
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("➕ Add New Student", type="primary", use_container_width=True):
            if len(st.session_state.students) < st.session_state.max_students:
                new_id = st.session_state.next_student_id
                st.session_state.students[new_id] = {
                    'ip': "",
                    'connected': False,
                    'monitoring': False,
                    'status_data': None,
                    'last_update': None
                }
                st.session_state.next_student_id += 1
                st.rerun()
            else:
                st.warning(f"Maximum {st.session_state.max_students} students allowed")
    
    with col2:
        st.metric("Total", len(st.session_state.students))
    
    st.markdown("---")
    
    # Display each student with controls
    for student_id in sorted(st.session_state.students.keys()):
        with st.container():
            st.markdown(f"### Student {student_id}")
            
            new_ip = st.text_input(
                f"IP Address",
                value=st.session_state.students[student_id]['ip'],
                placeholder="e.g., 192.168.1.100",
                key=f"ip_input_{student_id}"
            )
            
            # Update IP if changed
            if new_ip != st.session_state.students[student_id]['ip']:
                st.session_state.students[student_id]['ip'] = new_ip
                save_student_ips(st.session_state.students)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if not st.session_state.students[student_id]['connected']:
                    if st.button(f"🔗", key=f"connect_{student_id}", use_container_width=True, help="Connect"):
                        if new_ip:
                            with st.spinner(f"Connecting..."):
                                success, info = check_connection(new_ip)
                                if success:
                                    st.session_state.students[student_id]['connected'] = True
                                    st.success(f"✅")
                                else:
                                    st.error(f"❌")
                        else:
                            st.warning("Enter IP")
                else:
                    if st.button(f"🔴", key=f"disconnect_{student_id}", use_container_width=True, help="Disconnect"):
                        # Stop monitoring if active
                        if st.session_state.students[student_id]['monitoring']:
                            stop_monitoring(st.session_state.students[student_id]['ip'])
                            st.session_state.students[student_id]['monitoring'] = False
                        st.session_state.students[student_id]['connected'] = False
                        st.session_state.students[student_id]['status_data'] = None
                        st.rerun()
            
            with col2:
                if st.session_state.students[student_id]['connected']:
                    if not st.session_state.students[student_id]['monitoring']:
                        if st.button(f"▶️", key=f"start_{student_id}", use_container_width=True, help="Start"):
                            result = start_monitoring(st.session_state.students[student_id]['ip'])
                            if result.get('success'):
                                st.session_state.students[student_id]['monitoring'] = True
                                st.rerun()
                    else:
                        if st.button(f"⏹️", key=f"stop_{student_id}", use_container_width=True, help="Stop"):
                            result = stop_monitoring(st.session_state.students[student_id]['ip'])
                            if result.get('success'):
                                st.session_state.students[student_id]['monitoring'] = False
                                st.rerun()
            
            with col3:
                # Remove student button
                if st.button(f"🗑️", key=f"remove_{student_id}", use_container_width=True, help="Remove"):
                    # Stop and disconnect first
                    if st.session_state.students[student_id]['monitoring']:
                        stop_monitoring(st.session_state.students[student_id]['ip'])
                    del st.session_state.students[student_id]
                    save_student_ips(st.session_state.students)
                    st.rerun()
            
            # Connection status indicator
            if st.session_state.students[student_id]['connected']:
                st.success(f"🟢 Connected")
            else:
                st.warning(f"🔴 Not Connected")
            
            st.markdown("---")
    
    # Batch operations
    st.header("⚙️ Batch Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔗 Connect All", use_container_width=True):
            for student_id in st.session_state.students.keys():
                ip = st.session_state.students[student_id]['ip']
                if ip and not st.session_state.students[student_id]['connected']:
                    success, _ = check_connection(ip)
                    if success:
                        st.session_state.students[student_id]['connected'] = True
            st.rerun()
    
    with col2:
        if st.button("🔴 Disconnect All", use_container_width=True):
            for student_id in st.session_state.students.keys():
                if st.session_state.students[student_id]['monitoring']:
                    stop_monitoring(st.session_state.students[student_id]['ip'])
                    st.session_state.students[student_id]['monitoring'] = False
                st.session_state.students[student_id]['connected'] = False
            st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Start All", use_container_width=True, type="primary"):
            for student_id in st.session_state.students.keys():
                if st.session_state.students[student_id]['connected'] and \
                   not st.session_state.students[student_id]['monitoring']:
                    result = start_monitoring(st.session_state.students[student_id]['ip'])
                    if result.get('success'):
                        st.session_state.students[student_id]['monitoring'] = True
            st.rerun()
    
    with col2:
        if st.button("🛑 Stop All", use_container_width=True):
            for student_id in st.session_state.students.keys():
                if st.session_state.students[student_id]['monitoring']:
                    result = stop_monitoring(st.session_state.students[student_id]['ip'])
                    if result.get('success'):
                        st.session_state.students[student_id]['monitoring'] = False
            st.rerun()
    
    st.markdown("---")
    
    # Settings
    st.header("⚙️ Settings")
    st.session_state.sound_alerts = st.checkbox(
        "🔊 Sound Alerts",
        value=st.session_state.sound_alerts,
        help="Play sound when cheating detected"
    )
    
    st.session_state.auto_refresh = st.checkbox(
        "🔄 Auto Refresh",
        value=st.session_state.auto_refresh,
        help="Automatically refresh dashboard"
    )

# ============================================================================
# MAIN CONTENT - SUMMARY BAR
# ============================================================================

# Calculate summary statistics
total_students = len(st.session_state.students)
connected_count = sum(1 for s in st.session_state.students.values() if s['connected'])
monitoring_count = sum(1 for s in st.session_state.students.values() if s['monitoring'])
total_violations = sum(
    s['status_data'].get('total_violations', 0) 
    for s in st.session_state.students.values() 
    if s['status_data']
)
cheating_count = sum(
    1 for s in st.session_state.students.values() 
    if s['status_data'] and s['status_data'].get('is_cheating', False)
)

st.markdown(
    f'<div class="summary-bar">'
    f'👥 {connected_count}/{total_students} Connected | '
    f'▶️ {monitoring_count} Monitoring | '
    f'⚠️ {total_violations} Total Violations | '
    f'🚨 {cheating_count} Flagged for Cheating'
    f'</div>',
    unsafe_allow_html=True
)

# ============================================================================
# POLL ALL STUDENTS (if any monitoring)
# ============================================================================

if any(s['monitoring'] for s in st.session_state.students.values()):
    # Poll all connected students concurrently
    results = poll_all_students(st.session_state.students)
    
    # Update status data
    for student_id, result in results.items():
        if result['status_data']:
            st.session_state.students[student_id]['status_data'] = result['status_data']
            st.session_state.students[student_id]['last_update'] = datetime.now()
        elif result['error']:
            # Connection lost
            st.session_state.students[student_id]['connected'] = False
            st.session_state.students[student_id]['monitoring'] = False

# ============================================================================
# DYNAMIC GRID LAYOUT
# ============================================================================

# Determine number of columns based on student count
num_students = len(st.session_state.students)
if num_students == 0:
    st.info("👆 Click '➕ Add New Student' in the sidebar to start monitoring students")
else:
    # Use 3 columns for better layout, wrapping to new rows as needed
    num_cols = min(3, num_students)
    cols = st.columns(num_cols)
    
    for idx, student_id in enumerate(sorted(st.session_state.students.keys())):
        col_idx = idx % num_cols
        with cols[col_idx]:
            student = st.session_state.students[student_id]
            status_data = student['status_data']
            
            # Student header
            st.markdown(f"## Student {student_id}")
            
            # Determine status and color
            if not student['connected']:
                status_class = "status-disconnected"
                status_text = "DISCONNECTED"
            elif not student['monitoring']:
                status_class = "status-idle"
                status_text = "IDLE"
            elif status_data:
                is_cheating = status_data.get('is_cheating', False)
                if is_cheating:
                    status_class = "status-cheating"
                    status_text = "🚨 CHEATING"
                else:
                    status_class = "status-normal"
                    status_text = "✅ NORMAL"
            else:
                status_class = "status-idle"
                status_text = "WAITING..."
            
            # Status box
            st.markdown(
                f'<div class="status-box {status_class}">{status_text}</div>',
                unsafe_allow_html=True
            )
            
            # Metrics
            if status_data:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Violations", status_data.get('total_violations', 0))
                    st.metric("Face Violations", status_data.get('face_violations', 0))
                with col2:
                    st.metric("Confidence", f"{status_data.get('cheating_confidence', 0)}%")
                    st.metric("Object Violations", status_data.get('object_violations', 0))
                
                # Expandable details
                with st.expander("📊 View Details"):
                    st.markdown("#### Decision Engine")
                    if status_data.get('is_cheating'):
                        st.error(f"**Reason:** {status_data.get('cheating_reason', 'N/A')}")
                    else:
                        st.success("No cheating detected")
                    
                    st.markdown("---")
                    
                    # Face tracking data
                    st.markdown("#### 👁️ Face Tracking")
                    if 'face_data' in status_data:
                        face_data = status_data['face_data']
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Gaze Direction", face_data.get('gaze_direction', 'N/A'))
                            st.metric("Head Yaw", f"{face_data.get('head_yaw', 0):.1f}°")
                        with col2:
                            st.metric("Eye Velocity", f"{face_data.get('eye_velocity', 0):.2f}")
                            flagged = "🚨 YES" if face_data.get('flagged') else "✅ NO"
                            st.metric("Flagged", flagged)
                    else:
                        st.info("No data yet")
                    
                    st.markdown("---")
                    
                    # Object detection data
                    st.markdown("#### 📦 Object Detection")
                    if 'object_data' in status_data:
                        object_data = status_data['object_data']
                        col1, col2 = st.columns(2)
                        with col1:
                            detected = object_data.get('detected_objects', [])
                            st.metric("Detected", len(detected))
                            if detected:
                                st.write(", ".join(detected[:5]))
                        with col2:
                            prohibited = object_data.get('prohibited_objects', [])
                            st.metric("Prohibited", len(prohibited))
                            if prohibited:
                                st.error(", ".join(prohibited))
                        
                        st.metric("Inference Time", f"{object_data.get('inference_time', 0):.1f}ms")
                    else:
                        st.info("No data yet")
                    
                    st.markdown("---")
                    
                    # Recent events
                    st.markdown("#### 📋 Recent Events")
                    events = status_data.get('recent_events', [])
                    if events:
                        for event in events[:10]:
                            severity = event.get('severity', 'info')
                            emoji = "🚨" if severity == 'critical' else "⚠️" if severity == 'high' else "ℹ️"
                            st.text(f"{emoji} {event.get('timestamp')} - {event.get('message')}")
                    else:
                        st.info("No events yet")
            else:
                st.info("Not monitoring or no data available")
                if student['connected'] and not student['monitoring']:
                    st.warning("Click ▶️ Start button to begin monitoring")

# ============================================================================
# AUTO REFRESH
# ============================================================================

if st.session_state.auto_refresh and monitoring_count > 0:
    time.sleep(1)
    st.rerun()
