
import cv2 as cv
import numpy as np
import mediapipe as mp
import math
import socket
import argparse
import time
import csv
from datetime import datetime
import os
from AngleBuffer import AngleBuffer

import logging
import logging.handlers
import sys

#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------

# Parameters Documentation

## User-Specific Measurements
# USER_FACE_WIDTH: The horizontal distance between the outer edges of the user's cheekbones in millimeters. 
# This measurement is used to scale the 3D model points for head pose estimation.
# Measure your face width and adjust the value accordingly.
USER_FACE_WIDTH = 140  # [mm]

## Camera Parameters (not currently used in calculations)
# NOSE_TO_CAMERA_DISTANCE: The distance from the tip of the nose to the camera lens in millimeters.
# Intended for future use where accurate physical distance measurements may be necessary.
NOSE_TO_CAMERA_DISTANCE = 600  # [mm]

## Configuration Parameters
# PRINT_DATA: Enable or disable the printing of data to the console for debugging.

# DEFAULT_WEBCAM: Default camera source index. '0' usually refers to the built-in webcam.

# SHOW_ALL_FEATURES: If True, display all facial landmarks on the video feed.

# LOG_DATA: Enable or disable logging of data to a CSV file.

# LOG_ALL_FEATURES: If True, log all facial landmarks to the CSV file.

# ENABLE_HEAD_POSE: Enable the head position and orientation estimator.
ENABLE_HEAD_POSE = True

## Logging Configuration
# LOG_FOLDER: Directory where log files will be stored.

## Server Configuration
# SERVER_IP: IP address of the server for sending data via UDP (default is localhost).

# SERVER_PORT: Port number for the server to listen on.

## Blink Detection Parameters
# SHOW_ON_SCREEN_DATA: If True, display blink count and head pose angles on the video feed.
SHOW_ON_SCREEN_DATA = True

# TOTAL_BLINKS: Counter for the total number of blinks detected.

# EYES_BLINK_FRAME_COUNTER: Counter for consecutive frames with detected potential blinks.

# BLINK_THRESHOLD: Eye aspect ratio threshold below which a blink is registered.

# EYE_AR_CONSEC_FRAMES: Number of consecutive frames below the threshold required to confirm a blink.

## Head Pose Estimation Landmark Indices
# These indices correspond to the specific facial landmarks used for head pose estimation.
LEFT_EYE_IRIS = [474, 475, 476, 477]
RIGHT_EYE_IRIS = [469, 470, 471, 472]
LEFT_EYE_OUTER_CORNER = [33]
LEFT_EYE_INNER_CORNER = [133]
RIGHT_EYE_OUTER_CORNER = [362]
RIGHT_EYE_INNER_CORNER = [263]
RIGHT_EYE_POINTS = [33, 160, 159, 158, 133, 153, 145, 144]
LEFT_EYE_POINTS = [362, 385, 386, 387, 263, 373, 374, 380]
NOSE_TIP_INDEX = 4
CHIN_INDEX = 152
LEFT_EYE_LEFT_CORNER_INDEX = 33
RIGHT_EYE_RIGHT_CORNER_INDEX = 263
LEFT_MOUTH_CORNER_INDEX = 61
RIGHT_MOUTH_CORNER_INDEX = 291

## MediaPipe Model Confidence Parameters
# These thresholds determine how confidently the model must detect or track to consider the results valid.
# Lower values = more sensitive detection, higher values = more stable but may miss faces
MIN_DETECTION_CONFIDENCE = 0.5  # Reduced from 0.8 for better detection
MIN_TRACKING_CONFIDENCE = 0.5   # Reduced from 0.8 for better tracking

## Angle Normalization Parameters
# MOVING_AVERAGE_WINDOW: The number of frames over which to calculate the moving average for smoothing angles.
MOVING_AVERAGE_WINDOW = 15  # Increased for better smoothing

## Enhanced Tracking Parameters
# LANDMARK_SMOOTHING_WINDOW: Number of frames to smooth landmark positions
LANDMARK_SMOOTHING_WINDOW = 5

# FACE_DETECTION_TIMEOUT: Frames to wait before considering face lost
FACE_DETECTION_TIMEOUT = 10

# ENABLE_FRAME_PREPROCESSING: Apply image enhancement for better detection
ENABLE_FRAME_PREPROCESSING = True

# ENABLE_LANDMARK_SMOOTHING: Apply smoothing to landmark positions
ENABLE_LANDMARK_SMOOTHING = True

# Initial Calibration Flags
# initial_pitch, initial_yaw, initial_roll: Store the initial head pose angles for calibration purposes.
# calibrated: A flag indicating whether the initial calibration has been performed.
initial_pitch, initial_yaw, initial_roll = None, None, None
calibrated = False

# User-configurable parameters
PRINT_DATA = True  # Enable/disable data printing
DEFAULT_WEBCAM = 0  # Default webcam number
SHOW_ALL_FEATURES = True  # Show all facial landmarks if True
LOG_DATA = True  # Enable logging to CSV
LOG_ALL_FEATURES = True  # Log all facial landmarks if True
LOG_FOLDER = "logs"  # Folder to store log files
SHOW_WINDOW = True  # If False, run headless (no OpenCV GUI window)

# Server configuration
SERVER_IP = "127.0.0.1"  # Set the server IP address (localhost)
SERVER_PORT = 7070  # Set the server port

# eyes blinking variables
SHOW_BLINK_COUNT_ON_SCREEN = True  # Toggle to show the blink count on the video feed
TOTAL_BLINKS = 0  # Tracks the total number of blinks detected
EYES_BLINK_FRAME_COUNTER = (
    0  # Counts the number of consecutive frames with a potential blink
)
BLINK_THRESHOLD = 0.51  # Threshold for the eye aspect ratio to trigger a blink
EYE_AR_CONSEC_FRAMES = (
    2  # Number of consecutive frames below the threshold to confirm a blink
)
# SERVER_ADDRESS: Tuple containing the SERVER_IP and SERVER_PORT for UDP communication.
SERVER_ADDRESS = (SERVER_IP, SERVER_PORT)


#If set to false it will wait for your command (hittig 'r') to start logging.
IS_RECORDING = False  # Controls whether data is being logged

# Command-line arguments for camera source
parser = argparse.ArgumentParser(description="Eye Tracking Application")
parser.add_argument(
    "-c", "--camSource", help="Source of camera", default=str(DEFAULT_WEBCAM)
)
args = parser.parse_args()

# Iris and eye corners landmarks indices
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
L_H_LEFT = [33]  # Left eye Left Corner
L_H_RIGHT = [133]  # Left eye Right Corner
R_H_LEFT = [362]  # Right eye Left Corner
R_H_RIGHT = [263]  # Right eye Right Corner

# Blinking Detection landmark's indices.
# P0, P3, P4, P5, P8, P11, P12, P13
RIGHT_EYE_POINTS = [33, 160, 159, 158, 133, 153, 145, 144]
LEFT_EYE_POINTS = [362, 385, 386, 387, 263, 373, 374, 380]

# Face Selected points indices for Head Pose Estimation
_indices_pose = [1, 33, 61, 199, 263, 291]

# Server address for UDP socket communication
SERVER_ADDRESS = (SERVER_IP, 7070)


# Proctoring System Variables
GAZE_THRESHOLD_ANGLE = 15  # Degrees to consider as left/right/up gaze away from monitor
GAZE_ALERT_DURATION = 5  # Seconds to trigger alert (as requested)
last_gaze_direction = None  # 'left', 'right', 'up', or None
gaze_start_time = None  # Time when current gaze direction started
alert_triggered = False  # To avoid repeated alerts
proctoring_enabled = True  # Enable/disable proctoring system
violation_count = 0  # Count of violations detected

# Advanced Anti-Cheat Variables
PUPIL_DEVIATION_THRESHOLD = 30  # Pixels - threshold for pupil deviation from center
EYE_MOVEMENT_SMOOTHING = 5  # Frames for smoothing eye movement
pupil_history = []  # Store recent pupil positions for pattern analysis
eye_movement_velocity = 0  # Track eye movement speed
suspicious_eye_movements = 0  # Count suspicious eye-only movements
last_pupil_positions = None  # Previous frame pupil positions

# Calibration System Variables
CALIBRATION_MODE = False  # Whether we're in calibration mode
calibration_targets = []  # List of calibration points
current_calibration_target = 0  # Current target being calibrated
calibration_data = {}  # Store calibration results
calibration_completed = False  # Whether calibration is done
calibration_screen_bounds = {}  # Screen boundary data
calibration_eye_centers = {}  # Eye center positions for each target
calibration_start_time = None  # When calibration started

# Enhanced Tracking Variables
landmark_history = []  # Store recent landmark positions for smoothing
face_detection_failures = 0  # Count consecutive detection failures
last_valid_landmarks = None  # Store last valid landmarks for fallback
landmark_smoothing_buffer = []  # Buffer for landmark smoothing


# Function to calculate vector position
def vector_position(point1, point2):
    x1, y1 = point1.ravel()
    x2, y2 = point2.ravel()
    return x2 - x1, y2 - y1


def preprocess_frame(frame):
    """
    Apply image preprocessing to improve face detection accuracy.
    
    Args:
        frame: Input frame from camera
        
    Returns:
        Enhanced frame for better detection
    """
    if not ENABLE_FRAME_PREPROCESSING:
        return frame
    
    # Convert to LAB color space for better lighting normalization
    lab = cv.cvtColor(frame, cv.COLOR_BGR2LAB)
    l, a, b = cv.split(lab)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
    clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    # Merge channels back
    lab = cv.merge([l, a, b])
    enhanced = cv.cvtColor(lab, cv.COLOR_LAB2BGR)
    
    # Apply slight Gaussian blur to reduce noise
    enhanced = cv.GaussianBlur(enhanced, (3, 3), 0)
    
    return enhanced


def smooth_landmarks(landmarks, img_w, img_h):
    """
    Apply temporal smoothing to landmark positions for more stable tracking.
    
    Args:
        landmarks: Current landmark positions
        img_w, img_h: Image dimensions
        
    Returns:
        Smoothed landmark positions
    """
    global landmark_smoothing_buffer, last_valid_landmarks
    
    if not ENABLE_LANDMARK_SMOOTHING:
        return landmarks
    
    # Convert landmarks to numpy array
    current_landmarks = np.array(landmarks)
    
    # Add to smoothing buffer
    landmark_smoothing_buffer.append(current_landmarks)
    
    # Keep only recent frames
    if len(landmark_smoothing_buffer) > LANDMARK_SMOOTHING_WINDOW:
        landmark_smoothing_buffer.pop(0)
    
    # If we have enough frames, apply smoothing
    if len(landmark_smoothing_buffer) >= 3:
        # Calculate weighted average (more weight to recent frames)
        weights = np.linspace(0.5, 1.0, len(landmark_smoothing_buffer))
        weights = weights / np.sum(weights)
        
        # Initialize with proper dtype
        smoothed_landmarks = np.zeros_like(current_landmarks, dtype=np.float64)
        for i, landmark_set in enumerate(landmark_smoothing_buffer):
            smoothed_landmarks += weights[i] * landmark_set.astype(np.float64)
        
        # Convert to int after all calculations
        smoothed_landmarks_int = smoothed_landmarks.astype(np.int32)
        last_valid_landmarks = smoothed_landmarks_int
        return smoothed_landmarks_int
    else:
        # Not enough frames yet, use current landmarks
        last_valid_landmarks = current_landmarks
        return current_landmarks


def detect_face_quality(landmarks, img_w, img_h):
    """
    Assess the quality of face detection based on landmark positions.
    
    Args:
        landmarks: Detected landmark positions
        img_w, img_h: Image dimensions
        
    Returns:
        Quality score (0-1, higher is better)
    """
    if landmarks is None or len(landmarks) == 0:
        return 0.0
    
    # Check if key facial features are within reasonable bounds
    nose_tip = landmarks[NOSE_TIP_INDEX]
    left_eye = landmarks[LEFT_EYE_LEFT_CORNER_INDEX]
    right_eye = landmarks[RIGHT_EYE_RIGHT_CORNER_INDEX]
    
    # Check if landmarks are within image bounds
    margin = 50
    if (nose_tip[0] < margin or nose_tip[0] > img_w - margin or
        nose_tip[1] < margin or nose_tip[1] > img_h - margin):
        return 0.3
    
    # Check eye distance (should be reasonable)
    eye_distance = np.linalg.norm(left_eye - right_eye)
    expected_eye_distance = img_w * 0.15  # Roughly 15% of image width
    
    if eye_distance < expected_eye_distance * 0.5 or eye_distance > expected_eye_distance * 2.0:
        return 0.4
    
    # Check if face is roughly centered
    face_center_x = (left_eye[0] + right_eye[0]) / 2
    center_deviation = abs(face_center_x - img_w / 2) / (img_w / 2)
    
    if center_deviation > 0.7:  # Too far from center
        return 0.5
    
    # All checks passed
    return 1.0


def euclidean_distance_3D(points):
    """Calculates the Euclidean distance between two points in 3D space.

    Args:
        points: A list of 3D points.

    Returns:
        The Euclidean distance between the two points.

        # Comment: This function calculates the Euclidean distance between two points in 3D space.
    """

    # Get the three points.
    P0, P3, P4, P5, P8, P11, P12, P13 = points

    # Calculate the numerator.
    numerator = (
        np.linalg.norm(P3 - P13) ** 3
        + np.linalg.norm(P4 - P12) ** 3
        + np.linalg.norm(P5 - P11) ** 3
    )

    # Calculate the denominator.
    denominator = 3 * np.linalg.norm(P0 - P8) ** 3

    # Calculate the distance.
    distance = numerator / denominator

    return distance

def estimate_head_pose(landmarks, image_size):
    # Scale factor based on user's face width (assumes model face width is 150mm)
    scale_factor = USER_FACE_WIDTH / 150.0
    # 3D model points.
    model_points = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0 * scale_factor, -65.0 * scale_factor),        # Chin
        (-225.0 * scale_factor, 170.0 * scale_factor, -135.0 * scale_factor),     # Left eye left corner
        (225.0 * scale_factor, 170.0 * scale_factor, -135.0 * scale_factor),      # Right eye right corner
        (-150.0 * scale_factor, -150.0 * scale_factor, -125.0 * scale_factor),    # Left Mouth corner
        (150.0 * scale_factor, -150.0 * scale_factor, -125.0 * scale_factor)      # Right mouth corner
    ])
    

    # Camera internals
    focal_length = image_size[1]
    center = (image_size[1]/2, image_size[0]/2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]],
         [0, focal_length, center[1]],
         [0, 0, 1]], dtype = "double"
    )

    # Assuming no lens distortion
    dist_coeffs = np.zeros((4,1))

    # 2D image points from landmarks, using defined indices
    image_points = np.array([
        landmarks[NOSE_TIP_INDEX],            # Nose tip
        landmarks[CHIN_INDEX],                # Chin
        landmarks[LEFT_EYE_LEFT_CORNER_INDEX],  # Left eye left corner
        landmarks[RIGHT_EYE_RIGHT_CORNER_INDEX],  # Right eye right corner
        landmarks[LEFT_MOUTH_CORNER_INDEX],      # Left mouth corner
        landmarks[RIGHT_MOUTH_CORNER_INDEX]      # Right mouth corner
    ], dtype="double")


        # Solve for pose
    (success, rotation_vector, translation_vector) = cv.solvePnP(model_points, image_points, camera_matrix, dist_coeffs, flags=cv.SOLVEPNP_ITERATIVE)

    # Convert rotation vector to rotation matrix
    rotation_matrix, _ = cv.Rodrigues(rotation_vector)

    # Combine rotation matrix and translation vector to form a 3x4 projection matrix
    projection_matrix = np.hstack((rotation_matrix, translation_vector.reshape(-1, 1)))

    # Decompose the projection matrix to extract Euler angles
    _, _, _, _, _, _, euler_angles = cv.decomposeProjectionMatrix(projection_matrix)
    pitch, yaw, roll = euler_angles.flatten()[:3]


     # Normalize the pitch angle
    pitch = normalize_pitch(pitch)

    return pitch, yaw, roll

def normalize_pitch(pitch):
    """
    Normalize the pitch angle to be within the range of [-90, 90].

    Args:
        pitch (float): The raw pitch angle in degrees.

    Returns:
        float: The normalized pitch angle.
    """
    # Map the pitch angle to the range [-180, 180]
    if pitch > 180:
        pitch -= 360

    # Invert the pitch angle for intuitive up/down movement
    pitch = -pitch

    # Ensure that the pitch is within the range of [-90, 90]
    if pitch < -90:
        pitch = -(180 + pitch)
    elif pitch > 90:
        pitch = 180 - pitch
        
    pitch = -pitch

    return pitch


def initialize_calibration(img_w, img_h):
    """
    Initialize the calibration system with target points.
    
    Args:
        img_w, img_h: Image dimensions
        
    Returns:
        None
    """
    global calibration_targets, current_calibration_target, calibration_data, calibration_completed
    global calibration_screen_bounds, calibration_eye_centers, calibration_start_time
    
    # Define calibration targets (9-point calibration)
    margin = 50  # Margin from screen edges
    calibration_targets = [
        # Center
        (img_w // 2, img_h // 2, "center"),
        # Corners
        (margin, margin, "top_left"),
        (img_w - margin, margin, "top_right"),
        (margin, img_h - margin, "bottom_left"),
        (img_w - margin, img_h - margin, "bottom_right"),
        # Edges
        (img_w // 2, margin, "top_center"),
        (img_w // 2, img_h - margin, "bottom_center"),
        (margin, img_h // 2, "left_center"),
        (img_w - margin, img_h // 2, "right_center")
    ]
    
    current_calibration_target = 0
    calibration_data = {}
    calibration_completed = False
    calibration_screen_bounds = {
        'width': img_w,
        'height': img_h,
        'center_x': img_w // 2,
        'center_y': img_h // 2
    }
    calibration_eye_centers = {}
    calibration_start_time = time.time()
    
    print("\n CALIBRATION SYSTEM INITIALIZED")
    print("Please look at each blinking dot and press SPACE when you're looking at it.")
    print("This will help calibrate the system for your specific setup.")
    print("=" * 50)


def draw_calibration_target(frame, target_x, target_y, target_name, current_target, total_targets):
    """
    Draw a blinking calibration target on the frame.
    
    Args:
        frame: OpenCV frame
        target_x, target_y: Target position
        target_name: Name of the target
        current_target: Current target index
        total_targets: Total number of targets
        
    Returns:
        Modified frame
    """
    # Calculate blinking effect
    blink_speed = 2.0  # Blinks per second
    blink_phase = (time.time() * blink_speed) % 1.0
    is_visible = blink_phase < 0.7  # 70% visible, 30% hidden
    
    if is_visible:
        # Draw outer circle
        cv.circle(frame, (target_x, target_y), 25, (0, 255, 255), 3)
        # Draw inner circle
        cv.circle(frame, (target_x, target_y), 15, (0, 255, 255), -1)
        # Draw crosshair
        cv.line(frame, (target_x - 20, target_y), (target_x + 20, target_y), (0, 0, 0), 2)
        cv.line(frame, (target_x, target_y - 20), (target_x, target_y + 20), (0, 0, 0), 2)
    
    # Draw target label
    cv.putText(frame, f"Target {current_target + 1}/{total_targets}", 
               (target_x - 50, target_y - 40), cv.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 2)
    cv.putText(frame, target_name.replace('_', ' ').title(), 
               (target_x - 60, target_y + 50), cv.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
    
    # Draw instructions
    cv.putText(frame, "Look at the blinking dot and press SPACE", 
               (50, 50), cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2)
    cv.putText(frame, "Press 'q' to skip calibration", 
               (50, 80), cv.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 2)
    
    return frame


def process_calibration_data():
    """
    Process collected calibration data to create calibration parameters.
    
    Returns:
        dict: Calibration parameters
    """
    global calibration_data, calibration_eye_centers, calibration_screen_bounds
    
    if len(calibration_eye_centers) < 3:
        print(" Insufficient calibration data. Need at least 3 points.")
        return None
    
    # Calculate screen boundaries based on eye positions
    eye_positions = list(calibration_eye_centers.values())
    x_positions = [pos[0] for pos in eye_positions]
    y_positions = [pos[1] for pos in eye_positions]
    
    # Calculate calibration parameters
    calibration_params = {
        'screen_bounds': calibration_screen_bounds,
        'eye_centers': calibration_eye_centers,
        'calibration_targets': calibration_targets,
        'eye_range_x': (min(x_positions), max(x_positions)),
        'eye_range_y': (min(y_positions), max(y_positions)),
        'center_eye_position': calibration_eye_centers.get('center', (0, 0)),
        'calibration_timestamp': time.time()
    }
    
    # Calculate dynamic thresholds based on calibration
    x_range = max(x_positions) - min(x_positions)
    y_range = max(y_positions) - min(y_positions)
    
    # Set adaptive thresholds (20% of the calibrated range)
    calibration_params['adaptive_threshold_x'] = max(30, x_range * 0.2)
    calibration_params['adaptive_threshold_y'] = max(30, y_range * 0.2)
    
    print("\nCALIBRATION COMPLETED!")
    print(f"Screen size: {calibration_screen_bounds['width']}x{calibration_screen_bounds['height']}")
    print(f"Eye range X: {calibration_params['eye_range_x']}")
    print(f"Eye range Y: {calibration_params['eye_range_y']}")
    print(f"Adaptive threshold X: {calibration_params['adaptive_threshold_x']:.1f}")
    print(f"Adaptive threshold Y: {calibration_params['adaptive_threshold_y']:.1f}")
    print("=" * 50)
    
    return calibration_params


def save_calibration_data(calibration_params, filename="calibration_data.json"):
    """
    Save calibration data to a file.
    
    Args:
        calibration_params: Calibration parameters to save
        filename: Filename to save to
        
    Returns:
        bool: Success status
    """
    import json
    
    try:
        with open(filename, 'w') as f:
            json.dump(calibration_params, f, indent=2)
        print(f"💾 Calibration data saved to {filename}")
        return True
    except Exception as e:
        print(f" Error saving calibration data: {e}")
        return False


def load_calibration_data(filename="calibration_data.json"):
    """
    Load calibration data from a file.
    
    Args:
        filename: Filename to load from
        
    Returns:
        dict: Calibration parameters or None if failed
    """
    import json
    import os
    
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r') as f:
            calibration_params = json.load(f)
        print(f" Calibration data loaded from {filename}")
        return calibration_params
    except Exception as e:
        print(f" Error loading calibration data: {e}")
        return None


def analyze_eye_movement_pattern(l_cx, l_cy, r_cx, r_cy, img_w, img_h):
    """
    Advanced eye movement analysis to detect suspicious patterns.
    
    Args:
        l_cx, l_cy, r_cx, r_cy: Current pupil positions
        img_w, img_h: Image dimensions
        
    Returns:
        tuple: (suspicious_movement, movement_type, confidence)
    """
    global pupil_history, eye_movement_velocity, suspicious_eye_movements, last_pupil_positions
    
    current_pupil_center = ((l_cx + r_cx) / 2, (l_cy + r_cy) / 2)
    pupil_history.append(current_pupil_center)
    
    # Keep only recent history
    if len(pupil_history) > EYE_MOVEMENT_SMOOTHING:
        pupil_history.pop(0)
    
    suspicious_movement = False
    movement_type = "normal"
    confidence = 0.0
    
    if len(pupil_history) >= 3 and last_pupil_positions is not None:
        # Calculate movement velocity
        prev_center = last_pupil_positions
        current_center = current_pupil_center
        
        movement_distance = ((current_center[0] - prev_center[0])**2 + 
                           (current_center[1] - prev_center[1])**2)**0.5
        eye_movement_velocity = movement_distance
        
        # Calculate screen center and boundaries
        screen_center_x = img_w / 2
        screen_center_y = img_h / 2
        
        # Calculate deviation from screen center
        center_deviation_x = abs(current_center[0] - screen_center_x)
        center_deviation_y = abs(current_center[1] - screen_center_y)
        
        # Detect suspicious patterns
        if center_deviation_x > PUPIL_DEVIATION_THRESHOLD or center_deviation_y > PUPIL_DEVIATION_THRESHOLD:
            # High deviation from center - potential cheating
            suspicious_movement = True
            movement_type = "high_deviation"
            confidence = min(0.9, (center_deviation_x + center_deviation_y) / 100)
            
        elif eye_movement_velocity > 20:  # Fast eye movement
            # Rapid eye movement - could be scanning for answers
            suspicious_movement = True
            movement_type = "rapid_movement"
            confidence = min(0.8, eye_movement_velocity / 50)
            
        # Check for repetitive left-right scanning pattern
        if len(pupil_history) >= 5:
            x_positions = [pos[0] for pos in pupil_history[-5:]]
            y_positions = [pos[1] for pos in pupil_history[-5:]]
            
            # Check for oscillating pattern (left-right-left-right)
            x_variance = np.var(x_positions)
            y_variance = np.var(y_positions)
            
            if x_variance > 400 and y_variance < 100:  # High horizontal, low vertical variance
                suspicious_movement = True
                movement_type = "scanning_pattern"
                confidence = 0.7
                
        # Check for sustained off-center gaze
        if center_deviation_x > PUPIL_DEVIATION_THRESHOLD * 0.7:
            sustained_off_center = all(
                abs(pos[0] - screen_center_x) > PUPIL_DEVIATION_THRESHOLD * 0.5 
                for pos in pupil_history[-3:]
            )
            if sustained_off_center:
                suspicious_movement = True
                movement_type = "sustained_off_center"
                confidence = 0.8
    
    # Update last positions
    last_pupil_positions = current_pupil_center
    
    # Count suspicious movements
    if suspicious_movement:
        suspicious_eye_movements += 1
        if suspicious_eye_movements > 10:  # Threshold for alert
            print(f"  SUSPICIOUS EYE MOVEMENT DETECTED: {movement_type} (Count: {suspicious_eye_movements})")
    
    return suspicious_movement, movement_type, confidence




def calculate_screen_boundaries_from_calibration(calibration_data):
    """
    Calculate screen boundaries based on calibration data.
    This defines the acceptable viewing area within the monitor screen.
    
    Args:
        calibration_data: Dictionary containing calibration information
        
    Returns:
        dict: Screen boundary information with acceptable gaze zones
    """
    if not calibration_data or 'eye_centers' not in calibration_data:
        return None
    
    eye_centers = calibration_data['eye_centers']
    
    # Get boundary points from calibration
    screen_bounds = {
        'center': eye_centers.get('center', (0, 0)),
        'top_left': eye_centers.get('top_left', (0, 0)),
        'top_right': eye_centers.get('top_right', (0, 0)),
        'bottom_left': eye_centers.get('bottom_left', (0, 0)),
        'bottom_right': eye_centers.get('bottom_right', (0, 0)),
        'top_center': eye_centers.get('top_center', (0, 0)),
        'bottom_center': eye_centers.get('bottom_center', (0, 0)),
        'left_center': eye_centers.get('left_center', (0, 0)),
        'right_center': eye_centers.get('right_center', (0, 0))
    }
    
    # Calculate acceptable viewing zone (add 10% margin for natural eye movement)
    margin_factor = 0.1
    
    # Get extreme points
    x_coords = [pos[0] for pos in eye_centers.values()]
    y_coords = [pos[1] for pos in eye_centers.values()]
    
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    
    # Add margins
    x_margin = (max_x - min_x) * margin_factor
    y_margin = (max_y - min_y) * margin_factor
    
    acceptable_zone = {
        'left_boundary': min_x - x_margin,
        'right_boundary': max_x + x_margin,
        'top_boundary': min_y - y_margin,
        'bottom_boundary': max_y + y_margin,
        'center_x': screen_bounds['center'][0],
        'center_y': screen_bounds['center'][1],
        'width': max_x - min_x + (2 * x_margin),
        'height': max_y - min_y + (2 * y_margin)
    }
    
    return acceptable_zone



def is_gaze_within_screen_bounds(pupil_x, pupil_y, screen_boundaries):
    """
    Check if the current gaze position is within acceptable screen boundaries.
    
    Args:
        pupil_x, pupil_y: Current pupil position
        screen_boundaries: Screen boundary information from calibration
        
    Returns:
        tuple: (is_within_bounds, zone_description, deviation_severity)
    """
    if not screen_boundaries:
        # Fallback to basic center-based detection with larger tolerance
        return True, "screen_center", 0.0
    
    left_bound = screen_boundaries['left_boundary']
    right_bound = screen_boundaries['right_boundary']
    top_bound = screen_boundaries['top_boundary']
    bottom_bound = screen_boundaries['bottom_boundary']
    
    # Check if within acceptable screen area
    within_horizontal = left_bound <= pupil_x <= right_bound
    within_vertical = top_bound <= pupil_y <= bottom_bound
    within_bounds = within_horizontal and within_vertical
    
    # Determine zone and deviation severity
    if within_bounds:
        # Within acceptable screen area
        zone = "within_screen"
        deviation = 0.0
    else:
        # Outside acceptable area - determine direction and severity
        horizontal_deviation = 0
        vertical_deviation = 0
        
        if pupil_x < left_bound:
            horizontal_deviation = left_bound - pupil_x
            horizontal_direction = "left"
        elif pupil_x > right_bound:
            horizontal_deviation = pupil_x - right_bound
            horizontal_direction = "right"
        else:
            horizontal_direction = "center"
        
        if pupil_y < top_bound:
            vertical_deviation = top_bound - pupil_y
            vertical_direction = "up"
        elif pupil_y > bottom_bound:
            vertical_deviation = pupil_y - bottom_bound
            vertical_direction = "down"
        else:
            vertical_direction = "center"
        
        # Determine primary direction
        if horizontal_deviation > vertical_deviation:
            zone = f"off_screen_{horizontal_direction}"
            deviation = horizontal_deviation / screen_boundaries['width']
        else:
            zone = f"off_screen_{vertical_direction}"
            deviation = vertical_deviation / screen_boundaries['height']
        
        # Cap deviation at 1.0
        deviation = min(1.0, deviation)
    
    return within_bounds, zone, deviation



def detect_gaze_violation(pitch, yaw, roll, l_cx, l_cy, r_cx, r_cy, img_w, img_h, calibration_data):
    """
    Enhanced gaze violation detection that considers screen boundaries from calibration.
    Only triggers violations when gaze goes outside the calibrated screen area.
    
    Args:
        pitch, yaw, roll: Head pose angles
        l_cx, l_cy, r_cx, r_cy: Eye center coordinates
        img_w, img_h: Image dimensions
        calibration_data: Calibration data containing screen boundaries
        
    Returns:
        tuple: (violation_detected, gaze_status, confidence, cheat_detected, zone_info)
    """
    global last_gaze_direction, gaze_start_time, alert_triggered, violation_count
    global suspicious_eye_movements
    
    if not proctoring_enabled:
        return False, "forward", 0.0, False, "proctoring_disabled"
    
    current_time = time.time()
    violation_detected = False
    gaze_status = "within_screen"
    confidence = 0.0
    cheat_detected = False
    zone_info = "normal"
    
    # Calculate average pupil position
    pupil_x = (l_cx + r_cx) / 2
    pupil_y = (l_cy + r_cy) / 2
    
    # Get screen boundaries from calibration
    screen_boundaries = None
    if calibration_data and calibration_completed:
        screen_boundaries = calculate_screen_boundaries_from_calibration(calibration_data)
    
    # Check if gaze is within screen bounds
    within_bounds, zone_description, deviation_severity = is_gaze_within_screen_bounds(
        pupil_x, pupil_y, screen_boundaries
    )
    
    # Enhanced eye movement analysis
    suspicious_movement, movement_type, eye_confidence = analyze_eye_movement_pattern(
        l_cx, l_cy, r_cx, r_cy, img_w, img_h
    )
    
    # Head pose analysis (backup method)
    RELAXED_HEAD_THRESHOLD = 25  # Increased threshold for head pose
    head_looking_significantly_away = (
        abs(yaw) > RELAXED_HEAD_THRESHOLD or 
        abs(pitch) > RELAXED_HEAD_THRESHOLD
    )
    
    # Determine violation status
    if not within_bounds:
        # Check if looking down (allow this without triggering suspicion)
        is_looking_down = "down" in zone_description
        
        if is_looking_down:
            violation_detected = False
            gaze_status = "looking_down"
            confidence = 0.0
            cheat_detected = False
            zone_info = "allowed_looking_down"
        else:
            # Gaze is outside calibrated screen area and not looking down
            violation_detected = True
            gaze_status = zone_description
            confidence = min(0.9, 0.5 + deviation_severity)
            zone_info = f"deviation_{deviation_severity:.2f}"
            
            # Check if it's also a head movement (less suspicious) or eye-only (more suspicious)
            if not head_looking_significantly_away and deviation_severity > 0.3:
                cheat_detected = True  # Eye-only movement outside screen
                confidence = min(0.95, confidence + 0.2)
            
    elif suspicious_movement:
        # Within screen bounds but suspicious eye patterns
        violation_detected = True
        gaze_status = f"suspicious_{movement_type}"
        confidence = eye_confidence
        cheat_detected = True
        zone_info = "suspicious_pattern"
        
    elif head_looking_significantly_away:
        # Head turned significantly but eyes might still be on screen
        # Only flag as violation if both head and eyes indicate looking away
        if deviation_severity > 0.2:  # Some eye deviation too
            violation_detected = True
            gaze_status = "head_and_eye_deviation"
            confidence = 0.7
            zone_info = "combined_deviation"
    
    # Handle violation timing
    if violation_detected:
        if last_gaze_direction != gaze_status:
            # New type of violation
            last_gaze_direction = gaze_status
            gaze_start_time = current_time
            alert_triggered = False
            if PRINT_DATA:
                print(f" Potential violation detected: {gaze_status} (confidence: {confidence:.2f})")
        else:
            # Continuing same violation
            duration = current_time - gaze_start_time if gaze_start_time else 0
            if duration >= GAZE_ALERT_DURATION and not alert_triggered:
                alert_triggered = True
                violation_count += 1
                
                if cheat_detected:
                    print(f" CHEATING DETECTED: {gaze_status} for {duration:.1f}s! (Violation #{violation_count})")
                else:
                    print(f" SCREEN VIOLATION: Looking outside screen area for {duration:.1f}s! (Violation #{violation_count})")
    else:
        # No violation - reset tracking
        if last_gaze_direction:
            duration = current_time - gaze_start_time if gaze_start_time else 0
            if PRINT_DATA and duration > 2:  # Only log if it was a significant duration
                print(f"Returned to acceptable viewing area after {last_gaze_direction} for {duration:.1f}s")
        last_gaze_direction = None
        gaze_start_time = None
        alert_triggered = False
        gaze_status = "within_screen"
        zone_info = "normal"
    
    return violation_detected, gaze_status, confidence, cheat_detected, zone_info

def draw_screen_boundaries_overlay(frame, calibration_data):
    """
    Draw the acceptable viewing area overlay on the frame for debugging.
    
    Args:
        frame: OpenCV frame
        calibration_data: Calibration data
        
    Returns:
        Modified frame with overlay
    """
    if not calibration_data or not calibration_completed:
        return frame
    
    screen_boundaries = calculate_screen_boundaries_from_calibration(calibration_data)
    if not screen_boundaries:
        return frame
    
    # Draw acceptable viewing zone as a rectangle
    left = int(screen_boundaries['left_boundary'])
    right = int(screen_boundaries['right_boundary'])
    top = int(screen_boundaries['top_boundary'])
    bottom = int(screen_boundaries['bottom_boundary'])
    
    # Draw boundary rectangle (green = acceptable area)
    cv.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
    
    # Add label
    cv.putText(frame, "Acceptable Viewing Area", 
               (left, top - 10), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Draw center point
    center_x = int(screen_boundaries['center_x'])
    center_y = int(screen_boundaries['center_y'])
    cv.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
    
    return frame

# This function calculates the blinking ratio of a person.
def blinking_ratio(landmarks):
    """Calculates the blinking ratio of a person.

    Args:
        landmarks: A facial landmarks in 3D normalized.

    Returns:
        The blinking ratio of the person, between 0 and 1, where 0 is fully open and 1 is fully closed.

    """

    # Get the right eye ratio.
    right_eye_ratio = euclidean_distance_3D(landmarks[RIGHT_EYE_POINTS])

    # Get the left eye ratio.
    left_eye_ratio = euclidean_distance_3D(landmarks[LEFT_EYE_POINTS])

    # Calculate the blinking ratio.
    ratio = (right_eye_ratio + left_eye_ratio + 1) / 2

    return ratio


def setup_logging():
    """Configure logging to send to the central server and also print to terminal."""
    logger = logging.getLogger('EyeTracker-Script')  # Unique logger name
    logger.setLevel(logging.DEBUG)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Console handler for terminal output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)s %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Socket handler to send logs to central server (if available)
        try:
            socket_handler = logging.handlers.SocketHandler('127.0.0.1', 9020)
            socket_handler.setLevel(logging.INFO)
            logger.addHandler(socket_handler)
        except Exception:
            # If socket logging fails, continue with console logging only
            pass

        # Also ensure propagation to root is disabled to prevent duplicate logs
        logger.propagate = False

    return logger




# # Initializing MediaPipe face mesh and camera
# if PRINT_DATA:
#     print("Initializing the face mesh and camera...")
#     if PRINT_DATA:
#         head_pose_status = "enabled" if ENABLE_HEAD_POSE else "disabled"
#         print(f"Head pose estimation is {head_pose_status}.")
#         print("\n=== ADVANCED PROCTORING SYSTEM WITH CALIBRATION ===")
#         print(" CALIBRATION CONTROLS:")
#         print("Press 'k' - Start visual calibration (9-point system)")
#         print("Press SPACE - Advance to next calibration target")
#         print("Press 'l' - Load saved calibration data")
#         print("Press 'q' - Skip calibration and quit")
#         print("")
#         print(" PROCTORING CONTROLS:")
#         print("Press 'c' - Calibrate head pose (set current position as forward)")
#         print("Press 'r' - Start/Stop recording data")
#         print("Press 'p' - Toggle proctoring system ON/OFF")
#         print("Press 'v' - Reset violation count")
#         print("Press 's' - Reset suspicious movements count")
#         print("Press 'q' - Quit program")
#         print("=====================================================\n")
#         print(" CALIBRATION FEATURES:")
#         print("• 9-point visual calibration system")
#         print("• Blinking dots at screen edges and center")
#         print("• Adaptive thresholds based on your eye movement range")
#         print("• Screen size and boundary detection")
#         print("• Individual user calibration data storage")
#         print("")
#         print(" ANTI-CHEAT FEATURES:")
#         print("• Detects eye-only movements (head still, eyes moving)")
#         print("• Identifies scanning patterns (left-right-left-right)")
#         print("• Monitors rapid eye movements")
#         print("• Tracks sustained off-center gaze")
#         print("• Advanced pupil position analysis")
#         print("=====================================================\n")




# # Initializing socket for data transmission
# iris_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# # Preparing for CSV logging
# csv_data = []
# if not os.path.exists(LOG_FOLDER):
#     os.makedirs(LOG_FOLDER)

# # Column names for CSV file
# column_names = [
#     "Timestamp (ms)",
#     "Left Eye Center X",
#     "Left Eye Center Y",
#     "Right Eye Center X",
#     "Right Eye Center Y",
#     "Left Iris Relative Pos Dx",
#     "Left Iris Relative Pos Dy",
#     "Right Iris Relative Pos Dx",
#     "Right Iris Relative Pos Dy",
#     "Total Blink Count",
# ]
# # Add head pose columns if head pose estimation is enabled
# if ENABLE_HEAD_POSE:
#     column_names.extend(["Pitch", "Yaw", "Roll"])

# # Add proctoring columns
# column_names.extend([
#     "Gaze Direction",
#     "Violation Detected",
#     "Violation Count",
#     "Gaze Confidence",
#     "Proctoring Enabled",
#     "Cheat Detected",
#     "Suspicious Movements",
#     "Eye Movement Velocity"
# ])
    
# if LOG_ALL_FEATURES:
#     column_names.extend(
#         [f"Landmark_{i}_X" for i in range(468)]
#         + [f"Landmark_{i}_Y" for i in range(468)]
#     )

# # Check for existing calibration data on startup
# if PRINT_DATA:
#     print(" Checking for existing calibration data...")
#     loaded_calibration = load_calibration_data()
#     if loaded_calibration:
#         calibration_data = loaded_calibration
#         calibration_completed = True
#         print("Calibration data found and loaded!")
#         print("Press 'k' to recalibrate if needed.")
#     else:
#         print(" No calibration data found.")
#         print(" RECOMMENDED: Run calibration first for best accuracy!")
#         print("Press 'k' to start calibration, or 'q' to continue without calibration.")

# Main loop for video capture and processing
def main():
    log = setup_logging()
    log.info("Eye tracking script has started.")
    mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        static_image_mode=False,  # Optimize for video
    )
    cam_source = int(args.camSource)
    # Try to open the camera with a couple of backends for robustness
    cap = cv.VideoCapture(cam_source, cv.CAP_DSHOW)
    if not cap.isOpened():
        # Fallback: try MSMF and then default
        cap.release()
        cap = cv.VideoCapture(cam_source, cv.CAP_MSMF)
    if not cap.isOpened():
        cap.release()
        cap = cv.VideoCapture(cam_source)
    if not cap.isOpened():
        # Log to both our logger and console in case logging is remote-only
        msg = f"FATAL: Cannot open camera source {cam_source}. Try a different index (e.g., -c 0 or -c 1) or close other apps using the camera."
        try:
            log.error(msg)
        except Exception:
            pass
        print(msg)
        return

    log.info(f"Camera source {cam_source} opened. Warming up...")
    for _ in range(5):
        cap.read()
        time.sleep(0.1)

    # Verify we can read a frame
    ret, frame = cap.read()
    if not ret or frame is None:
        msg = (
            f"FATAL: Camera source {cam_source} opened but is not providing a video stream. "
            f"Is it in use by another application? Exiting."
        )
        try:
            log.error(msg)
        except Exception:
            pass
        print(msg)
        cap.release()
        return

    log.info("Camera warm-up complete. Starting main loop.")

    angle_buffer = AngleBuffer(size=MOVING_AVERAGE_WINDOW)  # Adjust size for smoothing

    # Ensure we modify module-level state and not create locals
    global calibrated, initial_pitch, initial_yaw, initial_roll, violation_count, suspicious_eye_movements, eye_movement_velocity, TOTAL_BLINKS, EYES_BLINK_FRAME_COUNTER, CALIBRATION_MODE, current_calibration_target, calibration_eye_centers, calibration_completed, calibration_data, face_detection_failures, IS_RECORDING, proctoring_enabled, last_gaze_direction, gaze_start_time, alert_triggered, pupil_history, last_pupil_positions
    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                break

            # Apply frame preprocessing for better detection
            enhanced_frame = preprocess_frame(frame)
            
            # Flipping the frame for a mirror effect
            # I think we better not flip to correspond with real world... need to make sure later...
            #frame = cv.flip(frame, 1)
            rgb_frame = cv.cvtColor(enhanced_frame, cv.COLOR_BGR2RGB)
            img_h, img_w = frame.shape[:2]
            # Follow MediaPipe best practice: mark image not writeable for performance
            rgb_frame.flags.writeable = False
            results = mp_face_mesh.process(rgb_frame)
            rgb_frame.flags.writeable = True

            if not results.multi_face_landmarks:
                    log.info("No face detected in the current frame.", extra={"gaze_direction": "no_face"})
                    time.sleep(0.1)  # Pause briefly to prevent high CPU usage
                    continue # Skip the rest of the loop for this frame

            if results.multi_face_landmarks:
                # Reset detection failure counter on successful detection
                face_detection_failures = 0
                
                # Get raw landmarks
                raw_mesh_points = np.array(
                    [
                        np.multiply([p.x, p.y], [img_w, img_h]).astype(np.int32)
                        for p in results.multi_face_landmarks[0].landmark
                    ]
                )
                
                # Check face detection quality
                face_quality = detect_face_quality(raw_mesh_points, img_w, img_h)
                
                # Apply smoothing if quality is good enough
                if face_quality > 0.3:  # Minimum quality threshold
                    mesh_points = smooth_landmarks(raw_mesh_points, img_w, img_h)
                else:
                    # Use last valid landmarks if current detection is poor
                    if last_valid_landmarks is not None:
                        mesh_points = last_valid_landmarks
                        if PRINT_DATA:
                            print(f" Poor face detection quality ({face_quality:.2f}), using last valid landmarks")
                    else:
                        mesh_points = raw_mesh_points
            else:
                # No face detected - increment failure counter
                face_detection_failures += 1
                
                # Use last valid landmarks if available and not too many failures
                if last_valid_landmarks is not None and face_detection_failures < FACE_DETECTION_TIMEOUT:
                    mesh_points = last_valid_landmarks
                    if PRINT_DATA and face_detection_failures % 10 == 0:  # Print every 10 frames
                        print(f" No face detected, using last valid landmarks (failures: {face_detection_failures})")
                else:
                    # Skip processing this frame
                    if PRINT_DATA and face_detection_failures == FACE_DETECTION_TIMEOUT:
                        print(" Face detection lost, skipping frame processing")
                    continue
            
            # Only process if we have valid landmarks
            if 'mesh_points' in locals():
                # CALIBRATION MODE
                if CALIBRATION_MODE:
                    if current_calibration_target < len(calibration_targets):
                        target_x, target_y, target_name = calibration_targets[current_calibration_target]
                        
                        # Draw calibration target
                        frame = draw_calibration_target(frame, target_x, target_y, target_name, 
                                                    current_calibration_target, len(calibration_targets))
                        
                        # Get current eye positions for calibration
                        (l_cx, l_cy), l_radius = cv.minEnclosingCircle(mesh_points[LEFT_EYE_IRIS])
                        (r_cx, r_cy), r_radius = cv.minEnclosingCircle(mesh_points[RIGHT_EYE_IRIS])
                        
                        # Store eye center for this target
                        eye_center = ((l_cx + r_cx) / 2, (l_cy + r_cy) / 2)
                        calibration_eye_centers[target_name] = eye_center
                        
                        # Draw eye tracking on calibration screen
                        cv.circle(frame, (int(l_cx), int(l_cy)), int(l_radius), (255, 0, 255), 2)
                        cv.circle(frame, (int(r_cx), int(r_cy)), int(r_radius), (255, 0, 255), 2)
                        cv.circle(frame, (int(eye_center[0]), int(eye_center[1])), 5, (0, 255, 0), -1)
                        
                        # Show progress
                        progress = (current_calibration_target + 1) / len(calibration_targets) * 100
                        cv.putText(frame, f"Calibration Progress: {progress:.0f}%", 
                                (50, img_h - 50), cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        # Calibration completed
                        calibration_params = process_calibration_data()
                        if calibration_params:
                            calibration_data = calibration_params
                            calibration_completed = True
                            save_calibration_data(calibration_params)
                            CALIBRATION_MODE = False
                            print(" Calibration completed! Starting proctoring system...")
                        else:
                            print(" Calibration failed. Please try again.")
                            CALIBRATION_MODE = False

                # Get the 3D landmarks from facemesh x, y and z(z is distance from 0 points)
                # just normalize values
                mesh_points_3D = np.array(
                    [[n.x, n.y, n.z] for n in results.multi_face_landmarks[0].landmark]
                )
                # getting the head pose estimation 3d points
                head_pose_points_3D = np.multiply(
                    mesh_points_3D[_indices_pose], [img_w, img_h, 1]
                )
                head_pose_points_2D = mesh_points[_indices_pose]

                # collect nose three dimension and two dimension points
                nose_3D_point = np.multiply(head_pose_points_3D[0], [1, 1, 3000])
                nose_2D_point = head_pose_points_2D[0]

                # create the camera matrix - IMPROVED VERSION
                # Use a more realistic focal length based on typical webcam FOV
                focal_length = img_w * 0.8  # More realistic focal length
                center_x = img_w / 2.0
                center_y = img_h / 2.0

                cam_matrix = np.array(
                    [[focal_length, 0, center_x], 
                    [0, focal_length, center_y], 
                    [0, 0, 1]], dtype=np.float64
                )

                # The distortion parameters
                dist_matrix = np.zeros((4, 1), dtype=np.float64)

                head_pose_points_2D = np.delete(head_pose_points_3D, 2, axis=1)
                head_pose_points_3D = head_pose_points_3D.astype(np.float64)
                head_pose_points_2D = head_pose_points_2D.astype(np.float64)
                # Solve PnP
                success, rot_vec, trans_vec = cv.solvePnP(
                    head_pose_points_3D, head_pose_points_2D, cam_matrix, dist_matrix
                )
                # Get rotational matrix
                rotation_matrix, jac = cv.Rodrigues(rot_vec)

                # Get angles
                angles, mtxR, mtxQ, Qx, Qy, Qz = cv.RQDecomp3x3(rotation_matrix)

                # Get the y rotation degree
                angle_x = angles[0] * 360
                angle_y = angles[1] * 360
                z = angles[2] * 360

                # if angle cross the values then
                threshold_angle = 10
                # See where the user's head tilting
                if angle_y < -threshold_angle:
                    face_looks = "Left"
                elif angle_y > threshold_angle:
                    face_looks = "Right"
                elif angle_x < -threshold_angle:
                    face_looks = "Down"
                elif angle_x > threshold_angle:
                    face_looks = "Up"
                else:
                    face_looks = "Forward"
                # Effective flags in headless vs windowed mode
                effective_show_all = SHOW_ALL_FEATURES and SHOW_WINDOW
                effective_show_on_screen = SHOW_ON_SCREEN_DATA and SHOW_WINDOW

                if SHOW_WINDOW:
                    if effective_show_on_screen:
                        cv.putText(
                            frame,
                            f"Face Looking at {face_looks}",
                            (img_w - 400, 80),
                            cv.FONT_HERSHEY_TRIPLEX,
                            0.8,
                            (0, 255, 0),
                            2,
                            cv.LINE_AA,
                        )
                    # Display the nose direction - FIXED VERSION
                    # Create a 3D point extending from nose tip in the direction of head orientation
                    nose_3D_direction = np.array([0, 0, 1000], dtype=np.float64)  # 1000mm forward
                    # Project the 3D direction point to 2D
                    nose_3d_projection, jacobian = cv.projectPoints(
                        nose_3D_direction.reshape(1, 1, 3), rot_vec, trans_vec, cam_matrix, dist_matrix
                    )
                    # Get the projected point
                    p1 = (int(nose_2D_point[0]), int(nose_2D_point[1]))  # Nose tip
                    p2 = (int(nose_3d_projection[0][0][0]), int(nose_3d_projection[0][0][1]))  # Direction point
                    # Draw the nose direction line
                    cv.line(frame, p1, p2, (255, 0, 255), 3)
                    # Add a small circle at the end of the line for better visibility
                    cv.circle(frame, p2, 5, (255, 0, 255), -1)
                    # Add calibration hint
                    if not calibrated and effective_show_on_screen:
                        cv.putText(frame, "Press 'c' to calibrate nose direction", 
                                (50, img_h - 100), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 255), 2)
                
                # getting the blinking ratio
                eyes_aspect_ratio = blinking_ratio(mesh_points_3D)
                # print(f"Blinking ratio : {ratio}")
                # checking if ear less then or equal to required threshold if yes then
                # count the number of frame frame while eyes are closed.
                if eyes_aspect_ratio <= BLINK_THRESHOLD:
                    EYES_BLINK_FRAME_COUNTER += 1
                # else check if eyes are closed is greater EYE_AR_CONSEC_FRAMES frame then
                # count the this as a blink
                # make frame counter equal to zero

                else:
                    if EYES_BLINK_FRAME_COUNTER > EYE_AR_CONSEC_FRAMES:
                        TOTAL_BLINKS += 1
                    EYES_BLINK_FRAME_COUNTER = 0
                
                # Display all facial landmarks if enabled (only when window is shown)
                if SHOW_WINDOW and effective_show_all:
                    for point in mesh_points:
                        cv.circle(frame, tuple(point), 1, (0, 255, 0), -1)
                # Process and display eye features (drawing only if window is shown)
                (l_cx, l_cy), l_radius = cv.minEnclosingCircle(mesh_points[LEFT_EYE_IRIS])
                (r_cx, r_cy), r_radius = cv.minEnclosingCircle(mesh_points[RIGHT_EYE_IRIS])
                center_left = np.array([l_cx, l_cy], dtype=np.int32)
                center_right = np.array([r_cx, r_cy], dtype=np.int32)

                # Highlighting the irises and corners of the eyes (only when window is shown)
                if SHOW_WINDOW:
                    cv.circle(
                        frame, center_left, int(l_radius), (255, 0, 255), 2, cv.LINE_AA
                    )  # Left iris
                    cv.circle(
                        frame, center_right, int(r_radius), (255, 0, 255), 2, cv.LINE_AA
                    )  # Right iris
                    cv.circle(
                        frame, mesh_points[LEFT_EYE_INNER_CORNER][0], 3, (255, 255, 255), -1, cv.LINE_AA
                    )  # Left eye right corner
                    cv.circle(
                        frame, mesh_points[LEFT_EYE_OUTER_CORNER][0], 3, (0, 255, 255), -1, cv.LINE_AA
                    )  # Left eye left corner
                    cv.circle(
                        frame, mesh_points[RIGHT_EYE_INNER_CORNER][0], 3, (255, 255, 255), -1, cv.LINE_AA
                    )  # Right eye right corner
                    cv.circle(
                        frame, mesh_points[RIGHT_EYE_OUTER_CORNER][0], 3, (0, 255, 255), -1, cv.LINE_AA
                    )  # Right eye left corner

                # Calculating relative positions
                l_dx, l_dy = vector_position(mesh_points[LEFT_EYE_OUTER_CORNER], center_left)
                r_dx, r_dy = vector_position(mesh_points[RIGHT_EYE_OUTER_CORNER], center_right)
                
                # PROCTORING SYSTEM: Detect gaze violations
                if ENABLE_HEAD_POSE:
                    # Get head pose angles for proctoring
                    proctoring_pitch, proctoring_yaw, proctoring_roll = estimate_head_pose(mesh_points, (img_h, img_w))
                    angle_buffer.add([proctoring_pitch, proctoring_yaw, proctoring_roll])
                    proctoring_pitch, proctoring_yaw, proctoring_roll = angle_buffer.get_average()
                    
                    # Adjust angles based on initial calibration
                    if calibrated:
                        proctoring_pitch -= initial_pitch
                        proctoring_yaw -= initial_yaw
                        proctoring_roll -= initial_roll
                    
                    # Detect gaze violations with anti-cheat measures
                    violation_detected, gaze_direction, confidence, cheat_detected, zone_info = detect_gaze_violation(
                        proctoring_pitch, proctoring_yaw, proctoring_roll,
                        l_cx, l_cy, r_cx, r_cy, img_w, img_h, calibration_data
                    )
                    
                    # Display proctoring status on screen (only when window is shown)
                    if SHOW_WINDOW and effective_show_on_screen:
                        # Gaze direction indicator
                        if cheat_detected:
                            gaze_color = (0, 255, 255)  # Yellow for suspicious movement
                            display_text = f"Gaze: {gaze_direction.upper()} (SUSPICIOUS)"
                        else:
                            gaze_color = (0, 255, 0) if gaze_direction == "forward" else (0, 0, 255)
                            display_text = f"Gaze: {gaze_direction.upper()}"
                        
                        cv.putText(frame, display_text, (img_w - 250, 200), 
                                cv.FONT_HERSHEY_DUPLEX, 0.7, gaze_color, 2, cv.LINE_AA)
                        
                        # Violation status
                        if violation_detected:
                            if alert_triggered:
                                if cheat_detected:
                                    cv.putText(frame, "ANTI-CHEAT ALERT!", (img_w - 300, 230), 
                                            cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 255), 2, cv.LINE_AA)
                                else:
                                    cv.putText(frame, "VIOLATION DETECTED!", (img_w - 300, 230), 
                                            cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 2, cv.LINE_AA)
                            else:
                                duration = time.time() - gaze_start_time if gaze_start_time else 0
                                cv.putText(frame, f"Looking {gaze_direction} ({duration:.1f}s)", (img_w - 300, 230), 
                                        cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 165, 255), 2, cv.LINE_AA)
                        
                        # Violation count
                        cv.putText(frame, f"Violations: {violation_count}", (img_w - 200, 260), 
                                cv.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 2, cv.LINE_AA)
                        
                        # Suspicious movements count
                        cv.putText(frame, f"Suspicious: {suspicious_eye_movements}", (img_w - 200, 290), 
                                cv.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 0), 2, cv.LINE_AA)
                        
                        # Proctoring status
                        status_color = (0, 255, 0) if proctoring_enabled else (128, 128, 128)
                        cv.putText(frame, f"Proctoring: {'ON' if proctoring_enabled else 'OFF'}", (img_w - 200, 320), 
                                cv.FONT_HERSHEY_DUPLEX, 0.6, status_color, 2, cv.LINE_AA)
                        
                        # Face detection quality indicator
                        if 'face_quality' in locals():
                            quality_color = (0, 255, 0) if face_quality > 0.7 else (0, 165, 255) if face_quality > 0.4 else (0, 0, 255)
                            cv.putText(frame, f"Face Quality: {face_quality:.2f}", (img_w - 200, 350), 
                                    cv.FONT_HERSHEY_DUPLEX, 0.6, quality_color, 2, cv.LINE_AA)
                        
                        # Detection status
                        if face_detection_failures > 0:
                            cv.putText(frame, f"Detection Issues: {face_detection_failures}", (img_w - 200, 380), 
                                    cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 255), 2, cv.LINE_AA)

                # Printing data if enabled
                if PRINT_DATA:
                    print(f"Total Blinks: {TOTAL_BLINKS}")
                    print(f"Left Eye Center X: {l_cx} Y: {l_cy}")
                    print(f"Right Eye Center X: {r_cx} Y: {r_cy}")
                    print(f"Left Iris Relative Pos Dx: {l_dx} Dy: {l_dy}")
                    print(f"Right Iris Relative Pos Dx: {r_dx} Dy: {r_dy}\n")
                    # Check if head pose estimation is enabled
                    if ENABLE_HEAD_POSE:
                        pitch, yaw, roll = estimate_head_pose(mesh_points, (img_h, img_w))
                        angle_buffer.add([pitch, yaw, roll])
                        pitch, yaw, roll = angle_buffer.get_average()

                        # Set initial angles on first successful estimation
                        if initial_pitch is None:
                            initial_pitch, initial_yaw, initial_roll = pitch, yaw, roll
                            calibrated = True
                            if PRINT_DATA:
                                print("Head pose recalibrated.")

                        # Adjust angles based on initial calibration
                        if calibrated:
                            pitch -= initial_pitch
                            yaw -= initial_yaw
                            roll -= initial_roll
                        
                        
                        if PRINT_DATA:
                            print(f"Head Pose Angles: Pitch={pitch}, Yaw={yaw}, Roll={roll}")



                # Logging data
                # if LOG_DATA:
                #     timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
                #     log_entry = [
                #         timestamp,
                #         l_cx,
                #         l_cy,
                #         r_cx,
                #         r_cy,
                #         l_dx,
                #         l_dy,
                #         r_dx,
                #         r_dy,
                #         TOTAL_BLINKS,
                #     ]  # Include blink count in CSV
                    
                #     # Append head pose data if enabled
                #     if ENABLE_HEAD_POSE:
                #         log_entry.extend([pitch, yaw, roll])
                    
                #     # Append proctoring data
                #     if ENABLE_HEAD_POSE and 'violation_detected' in locals():
                #         log_entry.extend([
                #             gaze_direction,
                #             violation_detected,
                #             violation_count,
                #             confidence,
                #             proctoring_enabled,
                #             cheat_detected,
                #             suspicious_eye_movements,
                #             eye_movement_velocity
                #         ])
                #     else:
                #         # Default values when proctoring data not available
                #         log_entry.extend(["forward", False, 0, 0.0, proctoring_enabled, False, 0, 0.0])
                    
                #     csv_data.append(log_entry)
                    
                #     if LOG_ALL_FEATURES:
                #         log_entry.extend([p for point in mesh_points for p in point])
                #         csv_data.append(log_entry)

                # # Sending data through socket
                # timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
                # # Create a packet with mixed types (int64 for timestamp and int32 for the rest)
                # packet = np.array([timestamp], dtype=np.int64).tobytes() + np.array([l_cx, l_cy, l_dx, l_dy], dtype=np.int32).tobytes()

                # SERVER_ADDRESS = ("127.0.0.1", 7070)
                # iris_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # iris_socket.sendto(packet, SERVER_ADDRESS)

                # print(f'Sent UDP packet to {SERVER_ADDRESS}: {packet}')


                # 1. Gather all your real-time data into a dictionary
                # Compute current violation duration (0 if none)
                current_duration = time.time() - gaze_start_time if gaze_start_time else 0
                log_data = {
                    "timestamp_ms": int(time.time() * 1000),
                    "left_eye_x": l_cx,
                    "left_eye_y": l_cy,
                    "right_eye_x": r_cx,
                    "right_eye_y": r_cy,
                    "left_iris_dx": l_dx,
                    "left_iris_dy": l_dy,
                    "right_iris_dx": r_dx,
                    "right_iris_dy": r_dy,
                    "total_blinks": TOTAL_BLINKS,
                    "pitch": pitch,
                    "yaw": yaw,
                    "roll": roll,
                    "gaze_direction": gaze_direction,
                    "violation_detected": violation_detected,
                    "flagged": bool(alert_triggered),
                    "violation_duration": float(current_duration),
                    "violation_count": violation_count,
                    "gaze_confidence": confidence,
                    "proctoring_enabled": proctoring_enabled,
                    "cheat_detected": cheat_detected,
                    "suspicious_movements": suspicious_eye_movements,
                    "eye_velocity": eye_movement_velocity
                }

                # 2. Log a simple message, passing the entire data dictionary to 'extra'
                log.info("Eye tracking update", extra=log_data)

            # Writing the on screen data on the frame (overlays only; only when window is shown)
                if SHOW_WINDOW and SHOW_ON_SCREEN_DATA:
                    if IS_RECORDING:
                        cv.circle(frame, (30, 30), 10, (0, 0, 255), -1)  # Red circle at the top-left corner
                    cv.putText(frame, f"Blinks: {TOTAL_BLINKS}", (30, 80), cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2, cv.LINE_AA)
                    if ENABLE_HEAD_POSE:
                        cv.putText(frame, f"Pitch: {int(pitch)}", (30, 110), cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2, cv.LINE_AA)
                        cv.putText(frame, f"Yaw: {int(yaw)}", (30, 140), cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2, cv.LINE_AA)
                        cv.putText(frame, f"Roll: {int(roll)}", (30, 170), cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 0), 2, cv.LINE_AA)

                # Displaying the processed frame (only when window is enabled)
                if SHOW_WINDOW:
                    cv.namedWindow("Eye Tracking", cv.WINDOW_NORMAL)
                    cv.setWindowProperty("Eye Tracking", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
                    cv.imshow("Eye Tracking", frame)
                    # Handle key presses
                    key = cv.waitKey(1) & 0xFF
                else:
                    key = -1  # No key handling in headless mode

                # Calibrate on 'c' key press
                if key == ord('c'):
                    initial_pitch, initial_yaw, initial_roll = pitch, yaw, roll
                    if PRINT_DATA:
                        print("Head pose recalibrated.")
                        print(" Nose direction line should now be straight when looking forward!")
                        
                # Inside the main loop, handle the 'r' key press
                if key == ord('r'):
                    IS_RECORDING = not IS_RECORDING
                    print("Recording started." if IS_RECORDING else "Recording paused.")
                
                # Toggle proctoring system on 'p' key press
                if key == ord('p'):
                    proctoring_enabled = not proctoring_enabled
                    print("Proctoring system ENABLED" if proctoring_enabled else "Proctoring system DISABLED")
                
                # Reset violation count on 'v' key press
                if key == ord('v'):
                    violation_count = 0
                    last_gaze_direction = None
                    gaze_start_time = None
                    alert_triggered = False
                    print("Violation count reset to 0")
                
                # Reset suspicious movements on 's' key press
                if key == ord('s'):
                    suspicious_eye_movements = 0
                    pupil_history = []
                    last_pupil_positions = None
                    print("Suspicious movements reset to 0")
                
                # Start calibration on 'k' key press
                if key == ord('k'):
                    if not CALIBRATION_MODE:
                        initialize_calibration(img_w, img_h)
                        CALIBRATION_MODE = True
                        current_calibration_target = 0
                        calibration_eye_centers = {}
                        print(" Starting calibration mode...")
                    else:
                        print(" Calibration already in progress!")
                
                # Advance calibration target on SPACE key press
                if key == ord(' ') and CALIBRATION_MODE:
                    if current_calibration_target < len(calibration_targets) - 1:
                        current_calibration_target += 1
                        target_name = calibration_targets[current_calibration_target][2]
                        print(f"Target {current_calibration_target} recorded. Moving to {target_name}...")
                    else:
                        # Complete calibration
                        calibration_params = process_calibration_data()
                        if calibration_params:
                            calibration_data = calibration_params
                            calibration_completed = True
                            save_calibration_data(calibration_params)
                            CALIBRATION_MODE = False
                            print(" Calibration completed! Starting proctoring system...")
                        else:
                            print(" Calibration failed. Please try again.")
                            CALIBRATION_MODE = False
                
                # Load calibration data on 'l' key press
                if key == ord('l'):
                    loaded_data = load_calibration_data()
                    if loaded_data:
                        calibration_data = loaded_data
                        calibration_completed = True
                        print(" Calibration data loaded successfully!")
                    else:
                        print(" No calibration data found. Run calibration first with 'k' key.")

                # Exit on 'q' key press (only works when window is shown)
                if SHOW_WINDOW and key == ord('q'):
                    if PRINT_DATA:
                        print("Exiting program...")
                    break

        except Exception as e: # <-- THIS ENTIRE BLOCK WAS ADDED
            # If ANY other error occurs, log it with the full traceback and exit.
            log.error("An unhandled exception occurred in the main loop.", exc_info=True)
            break # Exit the loop on a fatal error
    cap.release()
    if SHOW_WINDOW:
        cv.destroyAllWindows()
    log.info("Eye tracking script has shut down.")
            
if __name__ == '__main__':
    # This block ensures the code only runs when the script is executed directly
    try:
        main()
    except Exception as e:
        # This catches any critical error during the script's initialization
        log = setup_logging()
        log.error("A fatal error occurred outside the main loop.", exc_info=True)
        time.sleep(1) # Give the logger a moment to send the final error