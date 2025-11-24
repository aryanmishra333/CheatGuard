#!/usr/bin/env python3
"""
CheatGuard Multi-Student Proctoring Dashboard Launcher
Run this on the PROCTOR'S PC to monitor up to 3 students simultaneously
"""

import subprocess
import sys
import socket

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
    proctor_ip = get_server_ip()
    
    print("=" * 70)
    print("🛡️  CHEATGUARD MULTI-STUDENT MONITORING DASHBOARD")
    print("=" * 70)
    print(f"🖥️  Proctor PC IP: {proctor_ip}")
    print(f"🌐 Dashboard URL (Local): http://localhost:8501")
    print(f"🌐 Dashboard URL (Network): http://{proctor_ip}:8501")
    print("=" * 70)
    print("\n📋 SETUP INSTRUCTIONS:")
    print("   1. Start server_agent.py on each STUDENT PC")
    print("   2. Note each student's IP address")
    print("   3. Click '➕ Add New Student' to add monitoring slots")
    print("   4. Enter IPs and click Connect for each student")
    print("   5. Click 'Start All' to begin monitoring")
    print("\n💡 FEATURES:")
    print("   • Add students dynamically (up to 10)")
    print("   • Start with 1 student, add more as needed")
    print("   • Remove students anytime with 🗑️ button")
    print("   • Color-coded status (Green=Normal, Red=Cheating)")
    print("   • Individual and batch controls")
    print("   • Real-time violation tracking")
    print("   • Expandable detailed views")
    print("=" * 70)
    print("\nStarting Multi-Student Dashboard...")
    print("Press Ctrl+C to stop\n")
    
    # Start Streamlit with network access
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "multi_student_dashboard.py",
        "--server.address=0.0.0.0",
        "--server.port=8501"
    ])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping dashboard...")
        print("✅ Multi-Student Dashboard stopped")
