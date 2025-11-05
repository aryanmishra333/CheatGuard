import torch
from ultralytics import YOLO
import os
import sys

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
    # Perform inference using the specified device
    print(f"Starting detection...")
    results = model(source=camera_source, show=True, conf=0.3, save=True)
    print("✅ Detection completed successfully")
except Exception as e:
    print(f"❌ Error during detection: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
