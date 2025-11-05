#!/usr/bin/env python3
"""
CheatGuard Remote Dashboard - Runs on Proctor's PC
This dashboard connects to the student's PC and remotely controls the proctoring system
"""

import streamlit as st
import requests
import time
from datetime import datetime
import pandas as pd

# Page config
st.set_page_config(
    page_title="CheatGuard - Remote Control",
    page_icon="🛡️",
    layout="wide"
)

# Initialize session state
if 'server_ip' not in st.session_state:
    st.session_state.server_ip = ""
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'status_data' not in st.session_state:
    st.session_state.status_data = None
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False

# ============================================================================
# API FUNCTIONS
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
# UI STYLING
# ============================================================================

st.markdown("""
    <style>
    .status-box { 
        border-radius: 10px; 
        padding: 25px; 
        text-align: center; 
        color: white; 
        font-size: 24px; 
        font-weight: bold;
        margin-bottom: 20px;
    }
    .running { background-color: #28a745; }
    .idle { background-color: #6c757d; }
    .partial { background-color: #ffc107; color: black; }
    .error { background-color: #dc3545; }
    .violation-box {
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .violation-high { background-color: #f8d7da; border-left: 5px solid #dc3545; }
    .violation-medium { background-color: #fff3cd; border-left: 5px solid #ffc107; }
    .violation-low { background-color: #d1ecf1; border-left: 5px solid #17a2b8; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.title("🛡️ CheatGuard - Remote Proctoring Control")
st.markdown("---")

# ============================================================================
# SIDEBAR - CONNECTION
# ============================================================================

with st.sidebar:
    st.header("🔌 Server Connection")
    
    server_ip = st.text_input(
        "Student PC IP Address",
        value=st.session_state.server_ip,
        placeholder="e.g., 192.168.1.100",
        help="Enter the IP address shown on the student's PC"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔗 Connect", type="primary", use_container_width=True):
            if server_ip:
                st.session_state.server_ip = server_ip
                success, info = check_connection(server_ip)
                if success:
                    st.session_state.connected = True
                    st.success(f"✅ Connected!")
                    st.json(info)
                else:
                    st.session_state.connected = False
                    st.error(f"❌ Connection failed: {info}")
            else:
                st.warning("Please enter server IP")
    
    with col2:
        if st.button("🔴 Disconnect", use_container_width=True):
            st.session_state.connected = False
            st.session_state.monitoring_active = False
            st.info("Disconnected")
    
    if st.session_state.connected:
        st.success(f"🟢 Connected to {st.session_state.server_ip}")
    else:
        st.warning("🔴 Not connected")
    
    st.markdown("---")
    
    # Control buttons
    if st.session_state.connected:
        st.header("🎮 Controls")
        
        if not st.session_state.monitoring_active:
            if st.button("🚀 START MONITORING", type="primary", use_container_width=True):
                with st.spinner("Starting monitoring session..."):
                    result = start_monitoring(st.session_state.server_ip)
                    if result.get('success'):
                        st.success(result.get('message'))
                        st.session_state.monitoring_active = True
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.get('message')}")
        else:
            if st.button("🛑 STOP MONITORING", use_container_width=True):
                with st.spinner("Stopping monitoring session..."):
                    result = stop_monitoring(st.session_state.server_ip)
                    if result.get('success'):
                        st.info(result.get('message'))
                        st.session_state.monitoring_active = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.get('message')}")
    
    st.markdown("---")
    st.markdown("### 📖 Instructions")
    st.markdown("""
    1. Start `server_agent.py` on student's PC
    2. Note the IP address displayed
    3. Enter IP and click Connect
    4. Click START MONITORING
    5. Monitor violations in real-time
    """)

# ============================================================================
# MAIN CONTENT
# ============================================================================

if not st.session_state.connected:
    st.info("👆 Please connect to the student's PC using the sidebar")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🖥️ Student PC Setup")
        st.code("""
# On the student's PC:
python server_agent.py

# Note the displayed IP address
# Enter it in the sidebar
        """, language="bash")
    
    with col2:
        st.markdown("### 🔧 Requirements")
        st.markdown("""
        - Both PCs on same network
        - Port 5000 accessible
        - IP Webcam configured
        - Firewall allows connections
        """)

else:
    # Connected - show monitoring interface
    placeholder = st.empty()
    
    with placeholder.container():
        # Get status
        status_data, error = get_status(st.session_state.server_ip)
        
        if error:
            st.error(f"❌ Connection lost: {error}")
            st.session_state.connected = False
            time.sleep(2)
            st.rerun()
        
        if status_data:
            st.session_state.status_data = status_data
            
            # Status indicator
            status = status_data.get('status', 'Unknown')
            status_class = status.lower()
            st.markdown(
                f'<div class="status-box {status_class}">SYSTEM STATUS: {status.upper()}</div>',
                unsafe_allow_html=True
            )
            
            # Main metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Violations",
                    status_data.get('total_violations', 0),
                    delta="CRITICAL" if status_data.get('total_violations', 0) > 5 else None
                )
            
            with col2:
                st.metric(
                    "Face Violations",
                    status_data.get('face_violations', 0)
                )
            
            with col3:
                st.metric(
                    "Object Violations",
                    status_data.get('object_violations', 0)
                )
            
            with col4:
                face_running = status_data.get('face_tracking_running', False)
                object_running = status_data.get('object_detection_running', False)
                modules_running = sum([face_running, object_running])
                st.metric(
                    "Active Modules",
                    f"{modules_running}/2"
                )
            
            st.markdown("---")
            
            # Detailed data
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 👁️ Face Tracking")
                if 'face_data' in status_data:
                    face_data = status_data['face_data']
                    
                    if face_data.get('flagged'):
                        st.error("🚨 VIOLATION DETECTED")
                    else:
                        st.success("✅ Normal")
                    
                    st.metric("Gaze Direction", face_data.get('gaze_direction', 'N/A'))
                    st.metric("Head Yaw", f"{face_data.get('head_yaw', 0):.1f}°")
                    st.metric("Eye Velocity", f"{face_data.get('eye_velocity', 0):.2f}")
                else:
                    st.info("No data yet" if status == "Running" else "Not running")
            
            with col2:
                st.markdown("### 📦 Object Detection")
                if 'object_data' in status_data:
                    object_data = status_data['object_data']
                    
                    if object_data.get('violation_active'):
                        st.error("🚨 PROHIBITED OBJECTS DETECTED")
                    else:
                        st.success("✅ Normal")
                    
                    detected = object_data.get('detected_objects', [])
                    prohibited = object_data.get('prohibited_objects', [])
                    
                    st.metric("Detected Objects", len(detected))
                    st.metric("Prohibited Items", ', '.join(prohibited) if prohibited else 'None')
                    st.metric("Detection Time", f"{object_data.get('inference_time', 0):.1f}ms")
                else:
                    st.info("No data yet" if status == "Running" else "Not running")
            
            st.markdown("---")
            
            # Event log
            st.markdown("### 📋 Recent Events")
            events = status_data.get('recent_events', [])
            
            if events:
                for event in events[:15]:
                    severity_class = f"violation-{event.get('severity', 'low')}"
                    st.markdown(
                        f'<div class="violation-box {severity_class}">'
                        f'<strong>{event.get("timestamp")}</strong>: {event.get("message")}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No events yet")
    
    # Auto-refresh if monitoring is active
    if st.session_state.monitoring_active:
        time.sleep(1)
        st.rerun()
