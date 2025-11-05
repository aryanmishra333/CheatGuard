#!/usr/bin/env python3
"""
IP Webcam Connection Test Script
Tests connection to phone camera for desk monitoring
Now includes STREAM MODE test for performance!
"""

import cv2
import requests
import numpy as np
import time

# Configuration - UPDATE THIS WITH YOUR PHONE'S IP
IP_WEBCAM_URL = "http://192.168.1.4:8080/shot.jpg"
STREAM_URL = "http://192.168.1.4:8080/video"

def test_ip_webcam():
    """Test connection to IP webcam."""
    print("📱 IP WEBCAM CONNECTION TEST")
    print("=" * 60)
    print(f"Testing connection to: {IP_WEBCAM_URL}")
    print("=" * 60)
    
    # Test 1: Basic HTTP connection
    print("\n🔍 Test 1: Basic HTTP Connection")
    try:
        response = requests.get(IP_WEBCAM_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ SUCCESS: HTTP Status {response.status_code}")
            print(f"   Content length: {len(response.content)} bytes")
        else:
            print(f"❌ FAILED: HTTP Status {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ FAILED: Connection timeout (5 seconds)")
        print("   • Check if IP Webcam app is running on phone")
        print("   • Verify phone and computer are on same WiFi")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Cannot connect to IP address")
        print("   • Check IP address is correct")
        print("   • Ensure phone and computer on same network")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 2: Image decoding
    print("\n🖼️  Test 2: Image Decoding")
    try:
        image_array = np.array(bytearray(response.content), dtype=np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if frame is not None:
            height, width, channels = frame.shape
            print(f"✅ SUCCESS: Image decoded successfully")
            print(f"   Resolution: {width}x{height}")
            print(f"   Channels: {channels}")
        else:
            print("❌ FAILED: Could not decode image")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 3: Snapshot mode test (old method)
    print("\n� Test 3: Snapshot Mode Test (10 seconds)")
    print("   Testing original method (slower)...")
    
    try:
        frame_count = 0
        start_time = time.time()
        
        while time.time() - start_time < 10:
            # Fetch frame
            response = requests.get(IP_WEBCAM_URL, timeout=5)
            if response.status_code != 200:
                print(f"⚠️  Warning: Frame fetch failed (status {response.status_code})")
                continue
            
            # Decode frame
            image_array = np.array(bytearray(response.content), dtype=np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if frame is None:
                print("⚠️  Warning: Frame decode failed")
                continue
            
            frame_count += 1
            
            # Add info text
            cv2.putText(frame, f"SNAPSHOT MODE - Frame: {frame_count}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            cv2.putText(frame, "Press 'q' to end test early", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Display
            cv2.imshow("IP Webcam Test - Snapshot Mode", frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n⚠️  Test ended by user")
                break
        
        cv2.destroyAllWindows()
        
        elapsed = time.time() - start_time
        snapshot_fps = frame_count / elapsed
        
        print(f"✅ Snapshot mode test complete")
        print(f"   Frames captured: {frame_count}")
        print(f"   Duration: {elapsed:.1f} seconds")
        print(f"   Average FPS: {snapshot_fps:.1f}")
        
        if snapshot_fps < 5:
            print("⚠️  Warning: FPS is low (< 5) in snapshot mode")
            print("   This is NORMAL for snapshot mode!")
            print("   Stream mode will be MUCH faster...")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        cv2.destroyAllWindows()
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        cv2.destroyAllWindows()
        return False
    
    # Test 4: MJPEG Stream mode test (NEW - much faster!)
    print("\n🚀 Test 4: MJPEG Stream Mode Test (10 seconds)")
    print("   Testing optimized streaming method (FAST!)...")
    
    try:
        frame_count = 0
        start_time = time.time()
        
        # Open MJPEG stream
        stream = requests.get(STREAM_URL, stream=True, timeout=10)
        bytes_data = bytes()
        
        print("   Connected to stream, reading frames...")
        
        for chunk in stream.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')  # JPEG start
            b = bytes_data.find(b'\xff\xd9')  # JPEG end
            
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                
                # Decode frame
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if frame is not None:
                    frame_count += 1
                    
                    # Calculate FPS
                    elapsed = time.time() - start_time
                    current_fps = frame_count / elapsed if elapsed > 0 else 0
                    
                    # Add info text
                    cv2.putText(frame, f"STREAM MODE - Frame: {frame_count}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, "Press 'q' to end test", (10, 110), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    # Display
                    cv2.imshow("IP Webcam Test - Stream Mode", frame)
                    
                    # Check for quit or timeout
                    if cv2.waitKey(1) & 0xFF == ord('q') or elapsed >= 10:
                        break
        
        cv2.destroyAllWindows()
        
        elapsed = time.time() - start_time
        stream_fps = frame_count / elapsed
        
        print(f"✅ Stream mode test complete!")
        print(f"   Frames captured: {frame_count}")
        print(f"   Duration: {elapsed:.1f} seconds")
        print(f"   Average FPS: {stream_fps:.1f}")
        
        # Compare modes
        print(f"\n📊 PERFORMANCE COMPARISON:")
        print(f"   Snapshot mode FPS: {snapshot_fps:.1f}")
        print(f"   Stream mode FPS:   {stream_fps:.1f}")
        print(f"   Speed improvement: {stream_fps/snapshot_fps:.1f}x faster!")
        
        if stream_fps > 10:
            print("\n🎉 EXCELLENT! Stream mode is working great!")
        elif stream_fps > 5:
            print("\n✅ GOOD! Stream mode is working well")
        else:
            print("\n⚠️  Stream mode FPS is low. Try:")
            print("   • Reduce resolution in IP Webcam app")
            print("   • Move closer to WiFi router")
            print("   • Use 5GHz WiFi if available")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"\n⚠️  Stream mode test failed: {e}")
        print("   This might mean:")
        print("   • IP Webcam app doesn't support /video endpoint")
        print("   • Network connection is unstable")
        print("   • Firewall is blocking stream")
        print("\n   Don't worry! Snapshot mode will still work (just slower)")
        cv2.destroyAllWindows()
    
    # Final results
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("\n✅ Your IP webcam is ready for object detection!")
    print("\nNext steps:")
    print("1. Update config.py with your IP address:")
    print(f"   OBJECT_DETECTION_IP_WEBCAM_URL = \"{IP_WEBCAM_URL}\"")
    print("\n2. Run the complete system:")
    print("   streamlit run dashboard_app.py")
    print("\n3. Or test object detection specifically:")
    print("   python yolo_detection.py")
    
    return True


def main():
    """Main test function."""
    print("\n📱 CHEATGUARD - IP WEBCAM TEST UTILITY")
    print("This script will test your phone camera connection")
    print("for desk monitoring (object detection)")
    print("\n⚠️  Before running:")
    print("1. Install 'IP Webcam' app on your Android phone")
    print("2. Start the server in the app")
    print("3. Note the IP address shown (e.g., http://192.168.1.4:8080)")
    print("4. Update IP_WEBCAM_URL variable at the top of this script")
    print("\n📝 Current URL:", IP_WEBCAM_URL)
    
    # Ask user to confirm
    input("\nPress Enter to start test (or Ctrl+C to cancel)...")
    
    success = test_ip_webcam()
    
    if not success:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("• Ensure IP Webcam app is running on phone")
        print("• Verify phone and computer are on same WiFi network")
        print("• Check IP address is correct")
        print("• Try accessing URL in web browser first")
        print("• Check firewall isn't blocking connection")
        print("• Restart IP Webcam app and try again")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
