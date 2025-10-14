#!/usr/bin/env python3
"""
Proctoring System Test Script

This script demonstrates the proctoring system capabilities by running
the main eye tracking application with proctoring features enabled.

Usage:
    python proctoring_test.py

Features tested:
- Left/Right/Up gaze detection
- 10-second violation timer
- Real-time violation alerts
- Data logging with proctoring metrics
"""

import subprocess
import sys
import os

def main():
    print("=== PROCTORING SYSTEM TEST ===")
    print("This will run the eye tracking system with proctoring enabled.")
    print("\nTest Instructions:")
    print("1. Look straight ahead and press 'c' to calibrate")
    print("2. Look left, right, or up for more than 10 seconds")
    print("3. Watch for violation alerts")
    print("4. Press 'p' to toggle proctoring on/off")
    print("5. Press 'v' to reset violation count")
    print("6. Press 'q' to quit")
    print("\nStarting proctoring system...")
    
    try:
        # Run the main script
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running proctoring system: {e}")
    except KeyboardInterrupt:
        print("\nProctoring test interrupted by user.")
    except FileNotFoundError:
        print("Error: main.py not found. Make sure you're in the correct directory.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
