# CheatGuard - Remote Control Setup Guide

## 🎯 Architecture Overview

This is a **true remote control system** where the proctor can start/stop monitoring from their own computer.

```
PROCTOR'S PC                          STUDENT'S PC (Exam Machine)
┌────────────────────────┐           ┌──────────────────────────┐
│  proctor_dashboard.py  │──HTTP──▶  │  server_agent.py         │
│  (Streamlit)           │           │  ├─ Starts main.py       │
│  - START/STOP buttons  │◀──Data───│  ├─ Starts yolo_detection│
│  - View violations     │           │  ├─ Camera 0 (webcam)    │
│  - Real-time monitor   │           │  └─ Camera 1 (phone/CAMO)│
└────────────────────────┘           └──────────────────────────┘
```

### **Key Features:**
- ✅ Proctor controls everything remotely
- ✅ Student's PC runs headless (no UI needed)
- ✅ Start/Stop from proctor's dashboard
- ✅ Real-time violation monitoring
- ✅ Network-based communication

---

## 📦 Installation

### **On BOTH computers, install dependencies:**

```powershell
pip install -r requirements.txt
```

---

## 🚀 Setup Instructions

### **STEP 1: Configure Student's PC**

1. **Connect phone via USB** with CAMO app running (phone will be Camera 1)

2. **Add firewall rules** (Run as Administrator):
   ```powershell
   # Allow Flask API (port 5000)
   New-NetFirewallRule -DisplayName "CheatGuard API" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
   
   # Allow log servers (ports 9020, 9021)
   New-NetFirewallRule -DisplayName "CheatGuard Logs" -Direction Inbound -LocalPort 9020,9021 -Protocol TCP -Action Allow
   ```

3. **Start the server agent:**
   ```powershell
   python server_agent.py
   ```
   
   **Note the IP address displayed**, e.g., `192.168.1.100`

---

### **STEP 2: Configure Proctor's PC**

1. **Start the remote dashboard:**
   ```powershell
   streamlit run proctor_dashboard.py
   ```

2. **In the sidebar:**
   - Enter the student's PC IP (e.g., `192.168.1.100`)
   - Click **Connect**
   - Once connected, click **START MONITORING**

3. **Monitor in real-time:**
   - View live camera feeds status
   - See violations as they happen
   - Stop monitoring when exam ends

---

## 📱 CAMO Setup (Phone as USB Camera)

### **On Student's Phone:**

1. **Install CAMO app** (iOS or Android)
2. **Enable USB Debugging** on phone (Android: Developer Options)
3. **Connect phone via USB cable** to student's PC
4. **Start CAMO app** - phone will appear as Camera 1
5. **Position phone** to view desk area

**That's it!** No IP addresses or WiFi configuration needed. The phone appears as a regular USB camera.

---

## 🎮 How to Use

### **Before Exam:**

1. **Student's PC:**
   ```powershell
   python server_agent.py
   ```
   Leave it running

2. **Proctor's PC:**
   ```powershell
   streamlit run proctor_dashboard.py
   ```

### **During Exam:**

1. **Proctor clicks "START MONITORING"** in dashboard
2. **System automatically:**
   - Starts face tracking (Camera 0)
   - Starts object detection (IP webcam)
   - Begins logging violations

3. **Proctor monitors:**
   - Live gaze direction
   - Detected objects
   - Violations count
   - Real-time alerts

### **After Exam:**

1. **Proctor clicks "STOP MONITORING"**
2. **System automatically:**
   - Stops both detection scripts
   - Saves logs
   - Returns to idle state

---

## 📊 Dashboard Features

### **Connection Panel:**
- Enter student PC IP
- Connect/Disconnect buttons
- Connection status indicator

### **Control Panel:**
- START MONITORING (green button)
- STOP MONITORING (red button)
- Auto-refreshing status

### **Monitoring Panel:**
- **Face Tracking:**
  - Gaze direction
  - Head pose (yaw)
  - Eye velocity
  - Violation status

- **Object Detection:**
  - Detected objects count
  - Prohibited items list
  - Detection speed
  - Violation status

- **Event Log:**
  - Timestamped violations
  - Color-coded severity
  - Last 15 events visible

---

## 🔒 Firewall Configuration

### **Student's PC (Windows):**

```powershell
# Run as Administrator

# Flask API
New-NetFirewallRule -DisplayName "CheatGuard API" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow

# Log servers
New-NetFirewallRule -DisplayName "CheatGuard Logs" -Direction Inbound -LocalPort 9020,9021 -Protocol TCP -Action Allow
```

### **Check if ports are open:**

```powershell
# On proctor's PC, test connection:
Test-NetConnection -ComputerName STUDENT_IP -Port 5000
Test-NetConnection -ComputerName STUDENT_IP -Port 9020
Test-NetConnection -ComputerName STUDENT_IP -Port 9021
```

---

## 🐛 Troubleshooting

### **Cannot connect from proctor's PC:**

1. **Check firewall rules** on student's PC
2. **Verify both PCs on same network**
3. **Test API manually:**
   ```powershell
   # On proctor's PC
   curl http://STUDENT_IP:5000/api/info
   ```

### **CAMO camera not detected:**

- Ensure CAMO app is running on phone
- Check USB cable is connected properly
- Enable USB Debugging in phone settings
- Verify phone appears as Camera 1 in device manager

### **Monitoring won't start:**

- Check `main.py` and `yolo_detection.py` exist
- Verify CAMO camera is connected (Camera 1)
- Check camera permissions
- Look at terminal output on student's PC

### **Low FPS:**

- Use USB 3.0 port for better speed
- Reduce CAMO video quality if needed
- Close other apps on phone
- Ensure phone isn't in power-saving mode

---

## 📝 File Structure

```
Capstone/
├── server_agent.py          ← Run on STUDENT'S PC
├── proctor_dashboard.py     ← Run on PROCTOR'S PC
├── main.py                  ← Face tracking (auto-started)
├── yolo_detection.py        ← Object detection (auto-started)
├── dashboard_app.py         ← Old local dashboard (not needed)
├── config.py                ← Configuration
├── requirements.txt         ← Dependencies
└── diagnose_ip_webcam.py    ← Testing tool
```

---

## 🎯 Quick Start

### **Student's PC:**
```powershell
python server_agent.py
# Note the IP displayed
```

### **Proctor's PC:**
```powershell
streamlit run proctor_dashboard.py
# Enter student's IP
# Click Connect → START MONITORING
```

---

## ⚡ API Endpoints

The server agent exposes these endpoints:

- `GET /api/info` - Server information
- `GET /api/status` - Current system status
- `POST /api/start` - Start monitoring
- `POST /api/stop` - Stop monitoring

---

## ✅ Advantages of This System

1. **True Remote Control** - Proctor has full control
2. **No Student Interaction** - Student can't stop monitoring
3. **Centralized Monitoring** - One proctor monitors multiple students
4. **Clean Student PC** - No dashboards, just cameras
5. **Network Independent** - Works on any local network
6. **Real-time Updates** - Instant violation alerts
7. **Easy to Scale** - Add more student PCs easily

---

## 🔐 Security Notes

- Server agent only accepts commands from local network
- No authentication yet (add if needed)
- Firewall protects against external access
- Logs stored locally on student's PC

---

**That's it!** You now have a complete remote proctoring system! 🚀
