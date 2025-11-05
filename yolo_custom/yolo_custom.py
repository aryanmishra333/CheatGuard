import torch
from ultralytics import YOLO
import os
import sys
import cv2

# Check if GPU is available and select device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Determine model path (works whether run from root or yolo_custom folder)
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, "644_img.pt")
if not os.path.exists(model_path):
    # Try parent directory
    model_path = os.path.join(os.path.dirname(script_dir), "644_img.pt")

if not os.path.exists(model_path):
    print(f"❌ Error: Model file not found at {model_path}")
    sys.exit(1)

print(f"Loading model from: {model_path}")

# Load the YOLO model
model = YOLO(model_path)

# Move the model to the selected device
model.to(device)

# Get camera source from environment variable or default to 1
camera_source = int(os.environ.get('CAMERA_SOURCE', '1'))
print(f"Using camera source: {camera_source}")

try:
    print(f"Starting continuous detection...")
    print(f"Press 'q' to quit")
    
    # Open video capture
    cap = cv2.VideoCapture(camera_source)
    
    if not cap.isOpened():
        print(f"❌ Error: Could not open camera source {camera_source}")
        print("   Make sure CAMO Studio is running and phone is connected")
        sys.exit(1)
    
    print(f"✅ Camera opened successfully")
    
    frame_count = 0
    
    # Continuous detection loop
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("⚠️  Warning: Failed to read frame")
            break
        
        frame_count += 1
        
        # Run YOLO detection on frame
        results = model(frame, conf=0.3, verbose=True)

        # Get annotated frame
        annotated_frame = results[0].plot()

        # Display frame
        cv2.imshow('YOLO Object Detection', annotated_frame)

        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n⚠️  Stopping detection...")
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Detection stopped")
    
except KeyboardInterrupt:
    print("\n⚠️  Interrupted by user")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error during detection: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
