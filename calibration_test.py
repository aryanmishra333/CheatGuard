#!/usr/bin/env python3
"""
Enhanced Calibration System Test Script
This script demonstrates the visual calibration system with blinking dots
at screen edges and center for accurate proctoring setup.

Usage:
    python calibration_test.py

Features:
- 9-point visual calibration system with enhanced accuracy
- Screen-aware boundary detection
- Real-time eye tracking during calibration
- Adaptive threshold calculation based on individual eye movement patterns
- Calibration data storage and loading with validation
- Pre-calibration system checks
"""

import subprocess
import sys
import os
import json
import time
from datetime import datetime


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['cv2', 'numpy', 'mediapipe']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ MISSING DEPENDENCIES:")
        for pkg in missing_packages:
            if pkg == 'cv2':
                print(f"   • opencv-python (install with: pip install opencv-python)")
            else:
                print(f"   • {pkg} (install with: pip install {pkg})")
        return False
    
    print("✅ All required dependencies found.")
    return True


def check_camera_availability():
    """Check if camera is available and accessible."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                print("✅ Camera is accessible and working.")
                return True
            else:
                print("❌ Camera found but cannot capture frames.")
                return False
        else:
            print("❌ Cannot access camera. Please check if it's being used by another application.")
            return False
    except Exception as e:
        print(f"❌ Error checking camera: {e}")
        return False


def validate_calibration_data(data):
    """Validate the structure and content of calibration data."""
    required_keys = ['screen_bounds', 'eye_centers', 'eye_range_x', 'eye_range_y']
    
    for key in required_keys:
        if key not in data:
            return False, f"Missing required key: {key}"
    
    # Check if we have minimum required calibration points
    eye_centers = data.get('eye_centers', {})
    required_points = ['center', 'top_left', 'top_right', 'bottom_left', 'bottom_right']
    missing_points = [point for point in required_points if point not in eye_centers]
    
    if missing_points:
        return False, f"Missing calibration points: {missing_points}"
    
    # Check timestamp (warn if older than 7 days)
    timestamp = data.get('calibration_timestamp', 0)
    if timestamp > 0:
        age_days = (time.time() - timestamp) / (24 * 3600)
        if age_days > 7:
            return True, f"Warning: Calibration is {age_days:.1f} days old. Consider recalibrating."
    
    return True, "Calibration data is valid."


def check_calibration_data():
    """Check if calibration data exists and display detailed info."""
    if os.path.exists("calibration_data.json"):
        try:
            with open("calibration_data.json", 'r') as f:
                data = json.load(f)
            
            # Validate calibration data
            is_valid, message = validate_calibration_data(data)
            
            print("\n📁 EXISTING CALIBRATION DATA:")
            print(f"   Screen size: {data['screen_bounds']['width']}x{data['screen_bounds']['height']}")
            print(f"   Eye range X: ({data['eye_range_x'][0]:.1f}, {data['eye_range_x'][1]:.1f})")
            print(f"   Eye range Y: ({data['eye_range_y'][0]:.1f}, {data['eye_range_y'][1]:.1f})")
            print(f"   Adaptive threshold X: {data.get('adaptive_threshold_x', 'N/A'):.1f}")
            print(f"   Adaptive threshold Y: {data.get('adaptive_threshold_y', 'N/A'):.1f}")
            
            if 'calibration_timestamp' in data:
                cal_time = datetime.fromtimestamp(data['calibration_timestamp'])
                print(f"   Calibration date: {cal_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print(f"   Calibration points: {len(data.get('eye_centers', {}))}/9")
            
            if is_valid:
                if "Warning" in message:
                    print(f"⚠️  {message}")
                else:
                    print(f"✅ {message}")
            else:
                print(f"❌ {message}")
                
            return is_valid
            
        except json.JSONDecodeError:
            print("❌ Calibration file is corrupted (invalid JSON).")
            return False
        except Exception as e:
            print(f"❌ Error reading calibration data: {e}")
            return False
    else:
        print("\n❌ No calibration data found.")
        return False


def display_enhanced_instructions():
    """Display enhanced calibration instructions."""
    print("\n" + "=" * 65)
    print("🎯 ENHANCED SCREEN-AWARE PROCTORING CALIBRATION SYSTEM")
    print("=" * 65)
    print("This calibration will map your screen boundaries for accurate detection.")
    print("The system will ONLY flag violations when you look OUTSIDE your screen area.")
    print("")
    print("📋 CALIBRATION PROCESS:")
    print("   1. Sit in your normal exam/work position")
    print("   2. Ensure good lighting on your face")
    print("   3. Look directly at each blinking yellow dot")
    print("   4. Press SPACE when you're focused on the current dot")
    print("   5. Complete all 9 points for best accuracy")
    print("")
    print("🎯 CALIBRATION POINTS SEQUENCE:")
    print("   • Center of screen")
    print("   • Four corners (top-left, top-right, bottom-left, bottom-right)")
    print("   • Four edge midpoints (top, bottom, left, right)")
    print("")
    print("✅ AFTER CALIBRATION:")
    print("   • Green rectangle shows your acceptable viewing area")
    print("   • Natural reading/viewing within screen won't trigger alerts")
    print("   • Only off-screen behavior will be flagged as violations")
    print("   • System adapts to your individual eye movement patterns")
    print("")
    print("⚙️ KEYBOARD CONTROLS:")
    print("   • 'k' - Start/restart calibration")
    print("   • SPACE - Confirm current target, advance to next")
    print("   • 'l' - Load previously saved calibration")
    print("   • 'c' - Calibrate head pose (after eye calibration)")
    print("   • 'p' - Toggle proctoring system on/off")
    print("   • 'q' - Quit application")
    print("=" * 65)


def run_system_checks():
    """Run comprehensive system checks before calibration."""
    print("🔧 RUNNING SYSTEM CHECKS...")
    print("-" * 40)
    
    checks_passed = 0
    total_checks = 3
    
    # Check dependencies
    if check_dependencies():
        checks_passed += 1
    
    # Check camera
    if check_camera_availability():
        checks_passed += 1
    
    # Check main script exists
    if os.path.exists("main.py"):
        print("✅ Main proctoring script found.")
        checks_passed += 1
    else:
        print("❌ main.py not found in current directory.")
        print("   Make sure you're running this from the correct folder.")
    
    print(f"\n📊 SYSTEM CHECK RESULTS: {checks_passed}/{total_checks} passed")
    
    if checks_passed == total_checks:
        print("✅ All system checks passed. Ready for calibration!")
        return True
    else:
        print("❌ Some system checks failed. Please resolve issues before proceeding.")
        return False


def main():
    """Main function to run the calibration system."""
    print("🎯 CALIBRATION SYSTEM TEST")
    print("=" * 50)
    
    # Run system checks first
    if not run_system_checks():
        print("\n⚠️  System checks failed. Please fix the issues above.")
        input("Press Enter to continue anyway, or Ctrl+C to exit...")
    
    # Display enhanced instructions
    display_enhanced_instructions()
    
    # Check existing calibration
    print("\n🔍 CHECKING FOR EXISTING CALIBRATION...")
    has_valid_calibration = check_calibration_data()
    
    if has_valid_calibration:
        print("\n✅ Valid calibration data found!")
        print("   You can use existing calibration or recalibrate for better accuracy.")
        choice = input("\n❓ Use existing calibration? (y/n, default=y): ").strip().lower()
        if choice in ['n', 'no']:
            print("   Proceeding with new calibration...")
        else:
            print("   Using existing calibration. Press 'k' in the app to recalibrate if needed.")
    else:
        print("\n🎯 No valid calibration data found.")
        print("   Initial calibration is REQUIRED for accurate proctoring!")
    
    print(f"\n🚀 Starting enhanced proctoring system...")
    print("   Remember to press 'k' to start calibration once the camera feed appears.")
    print("-" * 50)
    
    try:
        # Run the main script
        result = subprocess.run([sys.executable, "main.py"], check=True)
        print("\n✅ Calibration system completed successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running calibration system: {e}")
        print("   Please check the main.py file and ensure all dependencies are installed.")
        
    except KeyboardInterrupt:
        print("\n🛑 Calibration test interrupted by user.")
        
    except FileNotFoundError:
        print("\n❌ Error: main.py not found.")
        print("   Make sure you're in the correct directory with the main proctoring script.")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        
    finally:
        # Final calibration check
        print("\n📋 POST-EXECUTION CALIBRATION CHECK:")
        final_check = check_calibration_data()
        if final_check:
            print("✅ Calibration data is now available for future use.")
        else:
            print("⚠️  No calibration data found. Consider running calibration again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Calibration test terminated by user. Goodbye!")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        print("Please check your Python environment and dependencies.")