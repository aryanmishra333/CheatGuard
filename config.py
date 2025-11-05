"""
CheatGuard Configuration File
Centralized configuration for both camera feeds and detection systems
"""

# ============================================================================
# CAMERA CONFIGURATION
# ============================================================================

# Face Tracking Camera (Main Proctoring - Webcam)
FACE_TRACKING_CAMERA_SOURCE = 0  # Usually 0 for built-in webcam

# Object Detection Camera (Desk View - Phone/IP Webcam)
OBJECT_DETECTION_USE_IP_WEBCAM = False  # Set to False to use regular camera
OBJECT_DETECTION_IP_WEBCAM_URL = "http://192.168.1.13:8080/video"  # Your phone's IP (28.4 FPS confirmed!)
OBJECT_DETECTION_CAMERA_SOURCE = 1  # Fallback if IP webcam fails

# Performance Optimization (for IP Webcam)
FRAME_SKIP = 2  # Process every Nth frame (1=all, 2=half, 3=third) - reduces CPU load
REDUCE_RESOLUTION = True  # Reduce frame size before YOLO processing
TARGET_WIDTH = 640  # Target width in pixels (smaller = faster, 640 is good balance)
# Note: Now using OpenCV's VideoCapture which handles streaming automatically

# ============================================================================
# DETECTION PARAMETERS
# ============================================================================

# Face Tracking & Gaze Detection
GAZE_THRESHOLD_ANGLE = 15  # Degrees to consider looking away
GAZE_ALERT_DURATION = 10   # Seconds before violation alert
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# Object Detection (YOLO)
YOLO_CONFIDENCE_THRESHOLD = 0.3
OBJECT_VIOLATION_DURATION = 3.0  # Seconds of continuous detection
PROHIBITED_OBJECTS = ['Chit', 'Phone', 'Earbuds']

# Anti-Cheat Parameters
PUPIL_DEVIATION_THRESHOLD = 30  # Pixels
EYE_MOVEMENT_SMOOTHING = 5      # Frames
RAPID_MOVEMENT_THRESHOLD = 20   # Pixels/frame

# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

# Socket Servers for Dashboard Communication
FACE_TRACKING_SOCKET_HOST = "127.0.0.1"
FACE_TRACKING_SOCKET_PORT = 9020

OBJECT_DETECTION_SOCKET_HOST = "127.0.0.1"
OBJECT_DETECTION_SOCKET_PORT = 9021

# IP Webcam Configuration
IP_WEBCAM_TIMEOUT = 5  # Seconds to wait for IP webcam response

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_FOLDER = "logs"
LOG_DATA = True
LOG_ALL_FEATURES = True

# ============================================================================
# DISPLAY CONFIGURATION
# ============================================================================

SHOW_WINDOW = True  # Set False for headless operation
SHOW_ON_SCREEN_DATA = True
SHOW_ALL_FEATURES = False

# ============================================================================
# CALIBRATION CONFIGURATION
# ============================================================================

CALIBRATION_FILE = "calibration_data.json"
MOVING_AVERAGE_WINDOW = 15  # Frames for angle smoothing

# ============================================================================
# IP WEBCAM SETUP INSTRUCTIONS
# ============================================================================
"""
To use your phone as the desk camera for object detection:

1. Install "IP Webcam" app on your Android phone
   (or similar app for iOS like "EpocCam")

2. Open the app and start the server
   - It will show you an IP address like: http://192.168.1.4:8080

3. Update OBJECT_DETECTION_IP_WEBCAM_URL above with your phone's IP

4. Make sure your phone and computer are on the SAME WiFi network

5. Test the connection:
   - Open a browser and go to: http://192.168.1.4:8080
   - You should see the phone camera feed

6. Position your phone to view your desk from above
   - Mount it or place it securely
   - Make sure it can see your desk, keyboard, and surrounding area

7. Run the system:
   python dashboard_app.py
   
Camera Setup:
- Webcam (Camera 0): Monitors your face for gaze tracking
- Phone (IP Webcam): Monitors your desk for prohibited objects
"""
