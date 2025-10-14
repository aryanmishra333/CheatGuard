# Proctoring System Implementation

## Overview

This proctoring system has been successfully implemented on top of the existing Python-Gaze-Face-Tracker. It detects when a person looks away from the monitor (left, right, or up) for more than 10 seconds and flags such behavior as a violation.

## Key Features

### ✅ **Dual Detection Methods**
- **Head Pose Analysis**: Uses MediaPipe's head pose estimation (pitch, yaw, roll angles)
- **Pupil Tracking**: Monitors pupil coordinates relative to eye corners
- **Combined Accuracy**: Both methods work together for maximum reliability

### ✅ **Violation Detection**
- **Left Gaze**: Head yaw < -15° OR pupils significantly left of center
- **Right Gaze**: Head yaw > +15° OR pupils significantly right of center  
- **Up Gaze**: Head pitch > +15° OR pupils significantly above center
- **Down Gaze**: Detected but NOT flagged (as per requirements)

### ✅ **10-Second Timer System**
- Continuous monitoring of gaze direction
- Violation triggered only after 10+ seconds of sustained looking away
- Real-time countdown display
- Automatic reset when returning to forward gaze

### ✅ **Real-Time Alerts**
- Visual indicators on screen
- Console alerts with violation count
- Color-coded status display
- Violation count tracking

### ✅ **Data Logging**
- All proctoring data logged to CSV
- Includes gaze direction, violation status, confidence levels
- Timestamped for analysis
- Compatible with existing logging system

## Usage Instructions

### 1. **Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the proctoring system
python main.py
```

### 2. **Calibration** (IMPORTANT)
1. Look straight ahead at the monitor
2. Press **'c'** to calibrate the system
3. This sets your current head position as "forward"

### 3. **Controls**
- **'c'** - Calibrate head pose (set current position as forward)
- **'r'** - Start/Stop recording data to CSV
- **'p'** - Toggle proctoring system ON/OFF
- **'v'** - Reset violation count to 0
- **'q'** - Quit program

### 4. **Testing the System**
1. Look left, right, or up for more than 10 seconds
2. Watch for the red "VIOLATION DETECTED!" alert
3. Check console for violation messages
4. Return to forward gaze to reset the timer

## Technical Implementation

### **Detection Algorithm**
```python
def detect_gaze_violation(pitch, yaw, roll, l_cx, l_cy, r_cx, r_cy, img_w, img_h):
    # Method 1: Head pose angles
    head_looking_left = yaw < -GAZE_THRESHOLD_ANGLE
    head_looking_right = yaw > GAZE_THRESHOLD_ANGLE
    head_looking_up = pitch > GAZE_THRESHOLD_ANGLE
    
    # Method 2: Pupil position analysis
    pupil_left_deviation = abs(l_cx - left_eye_center_x) + abs(r_cx - right_eye_center_x)
    pupil_up_deviation = abs(l_cy - eye_center_y) + abs(r_cy - eye_center_y)
    
    # Combined detection with confidence scoring
    # 10-second timer implementation
    # Violation alert system
```

### **Configuration Parameters**
```python
GAZE_THRESHOLD_ANGLE = 15      # Degrees for gaze detection
GAZE_ALERT_DURATION = 10       # Seconds before violation alert
proctoring_enabled = True       # Enable/disable system
```

### **Data Logging Columns**
- Timestamp (ms)
- Eye coordinates (Left/Right X, Y)
- Iris relative positions
- Blink count
- Head pose angles (Pitch, Yaw, Roll)
- **Gaze Direction** (left/right/up/down/forward)
- **Violation Detected** (True/False)
- **Violation Count** (Total violations)
- **Gaze Confidence** (0.0-1.0)
- **Proctoring Enabled** (True/False)

## Screen Display

The system shows real-time information on the video feed:

```
Gaze: FORWARD          ← Current gaze direction
Looking left (5.2s)    ← Countdown when looking away
Violations: 3          ← Total violation count
Proctoring: ON         ← System status
```

## Accuracy & Reliability

### **Strengths**
- ✅ Dual detection methods (head pose + pupil tracking)
- ✅ Calibration system for individual users
- ✅ Smoothing algorithms to reduce false positives
- ✅ Configurable thresholds
- ✅ Real-time feedback

### **Limitations**
- ⚠️ Requires good lighting for accurate pupil detection
- ⚠️ May need calibration adjustment for different users
- ⚠️ False positives possible with extreme head movements
- ⚠️ Requires user to stay within camera frame

## File Structure

```
├── main.py                    # Main application with proctoring
├── AngleBuffer.py            # Smoothing algorithms
├── proctoring_test.py        # Test script
├── PROCTORING_README.md      # This documentation
├── requirements.txt          # Dependencies
└── logs/                     # CSV data logs
    └── eye_tracking_log_*.csv
```

## Testing

Run the test script to verify functionality:
```bash
python proctoring_test.py
```

## Future Enhancements

1. **Machine Learning**: Train on user-specific patterns
2. **Sound Alerts**: Audio notifications for violations
3. **Web Interface**: Remote monitoring dashboard
4. **Multiple Users**: Support for multiple test-takers
5. **Advanced Analytics**: Detailed violation reports

## Troubleshooting

### **Common Issues**
1. **False Positives**: Recalibrate with 'c' key
2. **No Detection**: Check lighting and camera positioning
3. **System Not Working**: Ensure head pose estimation is enabled
4. **Poor Accuracy**: Adjust `GAZE_THRESHOLD_ANGLE` parameter

### **Debug Mode**
Set `PRINT_DATA = True` in main.py for detailed console output.

---

**Note**: This proctoring system is designed for educational and research purposes. Always ensure compliance with privacy laws and regulations when implementing in real-world scenarios.
