#!/usr/bin/env python3
"""
Debug version of server_agent.py with verbose logging
Use this to see what's happening when processes start
"""

import subprocess
import sys
import os
import time

print("=" * 70)
print("🔧 DEBUG: Testing Process Startup")
print("=" * 70)

# Test 1: Check if scripts exist
print("\n[Test 1] Checking if scripts exist...")
if os.path.exists('main.py'):
    print("   ✅ main.py found")
else:
    print("   ❌ main.py NOT found")
    sys.exit(1)

if os.path.exists('yolo_detection.py'):
    print("   ✅ yolo_detection.py found")
else:
    print("   ❌ yolo_detection.py NOT found")
    sys.exit(1)

# Test 2: Try starting main.py
print("\n[Test 2] Starting main.py...")
print("   Command:", sys.executable, "main.py")

try:
    face_process = subprocess.Popen(
        [sys.executable, 'main.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    
    print("   Process started, PID:", face_process.pid)
    print("   Waiting 5 seconds...")
    time.sleep(5)
    
    poll_result = face_process.poll()
    if poll_result is None:
        print("   ✅ main.py is still running!")
        print("   Check if you see a window with face tracking")
    else:
        print(f"   ❌ main.py exited with code: {poll_result}")
        print("   This means it crashed immediately")
    
except Exception as e:
    print(f"   ❌ Failed to start: {e}")
    sys.exit(1)

# Test 3: Try starting yolo_detection.py
print("\n[Test 3] Starting yolo_detection.py...")
print("   Command:", sys.executable, "yolo_detection.py")

try:
    yolo_process = subprocess.Popen(
        [sys.executable, 'yolo_detection.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )
    
    print("   Process started, PID:", yolo_process.pid)
    print("   Waiting 5 seconds...")
    time.sleep(5)
    
    poll_result = yolo_process.poll()
    if poll_result is None:
        print("   ✅ yolo_detection.py is still running!")
        print("   Check if you see a window with object detection")
    else:
        print(f"   ❌ yolo_detection.py exited with code: {poll_result}")
        print("   This means it crashed immediately")
    
except Exception as e:
    print(f"   ❌ Failed to start: {e}")

# Test 4: Check log servers
print("\n[Test 4] Checking if log servers are listening...")
import socket

for port in [9020, 9021]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        print(f"   ✅ Port {port} is listening")
    else:
        print(f"   ❌ Port {port} is NOT listening")
        print(f"      Start server_agent.py first!")

print("\n" + "=" * 70)
print("Debug test complete!")
print("=" * 70)
print("\nWhat to do next:")
print("1. If windows opened → processes are starting correctly")
print("2. If windows closed immediately → check camera permissions")
print("3. If ports not listening → start server_agent.py first")
print("4. Press Ctrl+C to stop the processes")
print("=" * 70)

input("\nPress Enter to terminate processes...")

face_process.terminate()
yolo_process.terminate()

print("Processes terminated")
