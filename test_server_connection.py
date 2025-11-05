#!/usr/bin/env python3
"""
Test script to verify server_agent.py is working correctly
Run this on the proctor's PC to test connection to student's PC
"""

import requests
import json
import sys

def test_server_connection(server_ip):
    """Test all API endpoints of the server agent"""
    
    print("=" * 70)
    print("🔧 CHEATGUARD SERVER AGENT CONNECTION TEST")
    print("=" * 70)
    print(f"Testing connection to: {server_ip}:5000\n")
    
    # Test 1: Server info
    print("[Test 1/3] Testing /api/info endpoint...")
    try:
        response = requests.get(f"http://{server_ip}:5000/api/info", timeout=5)
        if response.status_code == 200:
            info = response.json()
            print("✅ PASS: Server info retrieved")
            print(f"   Server IP: {info.get('server_ip')}")
            print(f"   API Port: {info.get('server_port')}")
            print(f"   Face Log Port: {info.get('face_log_port')}")
            print(f"   Object Log Port: {info.get('object_log_port')}")
            print(f"   Version: {info.get('version')}")
            print(f"   Status: {info.get('status')}")
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Is server_agent.py running on student's PC?")
        print("   2. Is firewall allowing port 5000?")
        print("   3. Are both PCs on same network?")
        return False
    
    # Test 2: Status endpoint
    print("\n[Test 2/3] Testing /api/status endpoint...")
    try:
        response = requests.get(f"http://{server_ip}:5000/api/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("✅ PASS: Status retrieved")
            print(f"   System Status: {status.get('status')}")
            print(f"   Face Tracking Running: {status.get('face_tracking_running')}")
            print(f"   Object Detection Running: {status.get('object_detection_running')}")
            print(f"   Face Violations: {status.get('face_violations')}")
            print(f"   Object Violations: {status.get('object_violations')}")
            print(f"   Total Violations: {status.get('total_violations')}")
            
            # Check for data
            if 'face_data' in status:
                print("   ✅ Face tracking data available")
                print(f"      Gaze: {status['face_data'].get('gaze_direction')}")
            else:
                print("   ⚠️  No face tracking data (may not be started yet)")
            
            if 'object_data' in status:
                print("   ✅ Object detection data available")
                print(f"      Objects: {status['object_data'].get('detected_objects')}")
            else:
                print("   ⚠️  No object detection data (may not be started yet)")
                
        else:
            print(f"❌ FAIL: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False
    
    # Test 3: Port accessibility
    print("\n[Test 3/3] Testing log server ports...")
    import socket
    
    ports = [5000, 9020, 9021]
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((server_ip, port))
            sock.close()
            
            if result == 0:
                print(f"   ✅ Port {port} is accessible")
            else:
                print(f"   ❌ Port {port} is not accessible")
                if port in [9020, 9021]:
                    print(f"      This may be OK if monitoring hasn't started yet")
        except Exception as e:
            print(f"   ❌ Port {port} test failed: {e}")
    
    print("\n" + "=" * 70)
    print("✅ CONNECTION TEST COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. If all tests pass, start the proctor dashboard:")
    print("   streamlit run proctor_dashboard.py")
    print("2. Enter the server IP and connect")
    print("3. Click START MONITORING")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    else:
        server_ip = input("Enter student's PC IP address: ").strip()
    
    if not server_ip:
        print("❌ No IP address provided")
        sys.exit(1)
    
    test_server_connection(server_ip)
