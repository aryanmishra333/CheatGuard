#!/usr/bin/env python3
"""
Quick test to verify CAMO camera is working as Camera 1
"""

import cv2

print("=" * 60)
print("CAMO CAMERA TEST")
print("=" * 60)

# Test Camera 0 (Webcam)
print("\n1. Testing Camera 0 (Webcam)...")
cap0 = cv2.VideoCapture(0)
if cap0.isOpened():
    ret, frame = cap0.read()
    if ret:
        print("   ✅ Camera 0 working!")
        print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
    else:
        print("   ❌ Camera 0 can't read frames")
    cap0.release()
else:
    print("   ❌ Camera 0 not accessible")

# Test Camera 1 (CAMO Phone)
print("\n2. Testing Camera 1 (CAMO Phone)...")
cap1 = cv2.VideoCapture(1)
if cap1.isOpened():
    ret, frame = cap1.read()
    if ret:
        print("   ✅ Camera 1 working!")
        print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
        
        # Show live preview
        print("\n   Opening preview window...")
        print("   Press 'q' to close")
        
        while True:
            ret, frame = cap1.read()
            if not ret:
                break
            
            cv2.putText(frame, "Camera 1 - CAMO (Press 'q' to quit)", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (0, 255, 0), 2)
            
            cv2.imshow('Camera 1 - CAMO Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap1.release()
        cv2.destroyAllWindows()
        print("\n   ✅ Camera 1 test complete!")
        
    else:
        print("   ❌ Camera 1 can't read frames")
        print("   Make sure CAMO app is running on phone")
        cap1.release()
else:
    print("   ❌ Camera 1 not accessible")
    print("\n   Troubleshooting:")
    print("   • Is CAMO app running on phone?")
    print("   • Is phone connected via USB?")
    print("   • Is USB Debugging enabled?")
    print("   • Try restarting CAMO app")

print("\n" + "=" * 60)
print("Camera Configuration:")
print("  Camera 0 = Webcam (for face tracking)")
print("  Camera 1 = Phone/CAMO (for desk monitoring)")
print("=" * 60)
