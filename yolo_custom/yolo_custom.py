import torch
from ultralytics import YOLO

# Check if GPU is available and select device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load the YOLO model
model = YOLO("644_img.pt")  # No 'device' argument here

# Move the model to the selected device
model.to(device)

# Perform inference using the specified device
results = model(source=1, show=True, conf=0.3, save=True)
