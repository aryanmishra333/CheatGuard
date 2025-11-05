#!/usr/bin/env python3
"""
CheatGuard Proctoring System - Network Startup Script
Run this to start the entire proctoring system with network access enabled
"""

import subprocess
import sys
import socket
import time

def get_server_ip():
    """Get the IP address of this machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    server_ip = get_server_ip()
    
    print("=" * 70)
    print("🛡️  CHEATGUARD PROCTORING SYSTEM")
    print("=" * 70)
    print(f"🖥️  Server IP Address: {server_ip}")
    print(f"🌐 Dashboard URL (Local): http://localhost:8501")
    print(f"🌐 Dashboard URL (Remote): http://{server_ip}:8501")
    print("=" * 70)
    print("\n📱 IMPORTANT: Update IP_WEBCAM_URL in yolo_detection.py with your phone's IP")
    print("   Current default: http://192.168.1.13:8080/video")
    print("\n📋 To use the system:")
    print("   1. This terminal: Dashboard will start automatically")
    print("   2. Open NEW terminal: python main.py (face tracking)")
    print("   3. Open NEW terminal: python yolo_detection.py (object detection)")
    print("\n🌐 For remote monitoring:")
    print(f"   Share this URL with proctors: http://{server_ip}:8501")
    print("=" * 70)
    print("\nStarting Streamlit dashboard with network access enabled...")
    print("Press Ctrl+C to stop\n")
    
    time.sleep(2)
    
    # Start Streamlit with network access
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "dashboard_app.py",
        "--server.address=0.0.0.0",
        "--server.port=8501"
    ])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping dashboard...")
        print("✅ CheatGuard system stopped")
