#!/usr/bin/env python3
"""
IP Webcam Diagnostic Tool
Helps identify and fix performance issues with IP webcam streaming
"""

import cv2
import requests
import numpy as np
import time
import sys

print("=" * 70)
print("IP WEBCAM DIAGNOSTIC TOOL")
print("=" * 70)

# Get IP address from user
ip_address = input("\nEnter your phone's IP address (e.g., 192.168.1.4): ").strip()
if not ip_address:
    ip_address = "192.168.1.13"  # Default

base_url = f"http://{ip_address}:8080"
print(f"\nTesting connection to: {base_url}")
print("=" * 70)

# Test 1: Basic connectivity
print("\n[Test 1/5] Testing basic connectivity...")
try:
    response = requests.get(f"{base_url}/", timeout=3)
    if response.status_code == 200:
        print("✅ PASS: Can connect to IP Webcam app")
    else:
        print(f"❌ FAIL: HTTP {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ FAIL: Cannot connect - {e}")
    print("\nPossible fixes:")
    print("  • Ensure IP Webcam app is running")
    print("  • Check both devices on same WiFi")
    print("  • Verify IP address is correct")
    sys.exit(1)

# Test 2: Video endpoint availability
print("\n[Test 2/5] Checking video stream endpoint...")
video_url = f"{base_url}/video"
try:
    response = requests.head(video_url, timeout=3)
    if response.status_code == 200:
        print(f"✅ PASS: Video stream available at {video_url}")
    else:
        print(f"⚠️  WARNING: Video endpoint returned {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Video endpoint not available - {e}")

# Test 3: OpenCV VideoCapture test
print("\n[Test 3/5] Testing OpenCV VideoCapture...")
print("This is what YOLO detection uses...")
cap = cv2.VideoCapture(video_url)

if not cap.isOpened():
    print("❌ FAIL: OpenCV cannot open stream")
    print("\nPossible fixes:")
    print("  • Try different URL format")
    print("  • Check IP Webcam settings")
    print("  • Update OpenCV: pip install --upgrade opencv-python")
    cap.release()
    sys.exit(1)

print("✅ PASS: OpenCV connected to stream")

# Test 4: Frame reading speed test
print("\n[Test 4/5] Testing frame reading speed (10 seconds)...")
frame_count = 0
start_time = time.time()
failed_reads = 0

print("Reading frames...")
while time.time() - start_time < 10:
    ret, frame = cap.read()
    if ret and frame is not None:
        frame_count += 1
    else:
        failed_reads += 1
    
    # Show progress every 2 seconds
    elapsed = time.time() - start_time
    if int(elapsed) % 2 == 0 and int(elapsed) > 0 and frame_count > 0:
        current_fps = frame_count / elapsed
        print(f"  {int(elapsed)}s: {frame_count} frames, {current_fps:.1f} FPS")
        time.sleep(0.1)  # Prevent multiple prints

cap.release()

elapsed = time.time() - start_time
fps = frame_count / elapsed

print(f"\n📊 Results:")
print(f"  Frames received: {frame_count}")
print(f"  Failed reads: {failed_reads}")
print(f"  Average FPS: {fps:.1f}")

if fps < 5:
    print("\n❌ POOR: FPS is very low (< 5)")
    print("\nRecommended fixes:")
    print("  1. Reduce resolution in IP Webcam app:")
    print("     • Open app → Video preferences → Resolution → 640x480")
    print("  2. Reduce quality:")
    print("     • Video preferences → Quality → 50-60%")
    print("  3. Move closer to WiFi router")
    print("  4. Use 5GHz WiFi if available")
    print("  5. Close other apps on phone")
elif fps < 10:
    print("\n⚠️  FAIR: FPS is acceptable but could be better (5-10)")
    print("\nOptional improvements:")
    print("  • Move closer to WiFi router")
    print("  • Use 5GHz WiFi band")
    print("  • Reduce video quality in app")
elif fps < 15:
    print("\n✅ GOOD: FPS is decent (10-15)")
    print("  This should work well with frame skipping enabled")
else:
    print("\n🎉 EXCELLENT: FPS is great (15+)")
    print("  Your setup is optimal!")

# Test 5: Display test with frame skip simulation
print("\n[Test 5/5] Testing with frame skip (like YOLO mode)...")
print("Opening video window for 5 seconds...")

cap = cv2.VideoCapture(video_url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

frame_count = 0
processed_count = 0
start_time = time.time()
FRAME_SKIP = 2

while time.time() - start_time < 5:
    ret, frame = cap.read()
    if not ret or frame is None:
        continue
    
    frame_count += 1
    
    # Simulate frame skipping
    if frame_count % FRAME_SKIP == 0:
        processed_count += 1
        # Simulate YOLO processing delay
        time.sleep(0.03)  # ~30ms processing time
        
        # Add overlay
        cv2.putText(frame, f"Frame: {frame_count} (Processed)", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv2.putText(frame, f"Frame: {frame_count} (Skipped)", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    cv2.imshow("Frame Skip Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

elapsed = time.time() - start_time
effective_fps = processed_count / elapsed

print(f"\n📊 Frame Skip Results:")
print(f"  Total frames: {frame_count}")
print(f"  Processed (YOLO): {processed_count}")
print(f"  Effective FPS: {effective_fps:.1f}")

if effective_fps >= 5:
    print(f"\n✅ SUCCESS: Your setup should work well!")
    print(f"  Expected FPS with YOLO: ~{effective_fps:.1f}")
else:
    print(f"\n❌ WARNING: FPS may still be low with YOLO")
    print(f"  Try increasing FRAME_SKIP to 3 or 4")

# Summary and recommendations
print("\n" + "=" * 70)
print("DIAGNOSTIC SUMMARY")
print("=" * 70)
print(f"\n✅ URL to use in config.py:")
print(f"   OBJECT_DETECTION_IP_WEBCAM_URL = \"{video_url}\"")
print(f"\n📊 Performance:")
print(f"   Raw stream FPS: {fps:.1f}")
print(f"   With frame skip: {effective_fps:.1f}")

if fps < 10:
    print(f"\n⚙️  Recommended settings in config.py:")
    print(f"   FRAME_SKIP = 3  # Process every 3rd frame")
    print(f"   REDUCE_RESOLUTION = True")
    print(f"   TARGET_WIDTH = 416  # Smaller for faster processing")
else:
    print(f"\n⚙️  Recommended settings in config.py:")
    print(f"   FRAME_SKIP = 2  # Process every 2nd frame")
    print(f"   REDUCE_RESOLUTION = True")
    print(f"   TARGET_WIDTH = 640  # Good balance")

print("\n" + "=" * 70)
print("Next step: Run 'python yolo_detection.py'")
print("=" * 70)
