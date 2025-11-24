# CheatGuard Multi-Student Monitoring Setup

## 🎯 Overview

The multi-student monitoring system allows **one proctor to monitor up to 3 students simultaneously** from a single dashboard. Each student runs their own instance of the CheatGuard system, and the proctor can control and monitor all of them in real-time.

## 🏗️ Architecture

```
PROCTOR'S PC                                    STUDENT PCs (3 machines)
┌─────────────────────────────┐               
│ multi_student_dashboard.py  │──┐            ┌─────────────────────────┐
│  ┌───────────────────────┐  │  │            │ Student 1 (192.168.1.10)│
│  │  Student 1  │ Green   │  │──┼───HTTP────▶│ • server_agent.py       │
│  │  0 Violations         │  │  │            │ • main.py (face)        │
│  └───────────────────────┘  │  │            │ • yolo_detection.py     │
│  ┌───────────────────────┐  │  │            └─────────────────────────┘
│  │  Student 2  │ Red     │  │  │
│  │  5 Violations         │  │  │            ┌─────────────────────────┐
│  └───────────────────────┘  │  │            │ Student 2 (192.168.1.11)│
│  ┌───────────────────────┐  │  ├───HTTP────▶│ • server_agent.py       │
│  │  Student 3  │ Green   │  │  │            │ • main.py (face)        │
│  │  1 Violation          │  │  │            │ • yolo_detection.py     │
│  └───────────────────────┘  │  │            └─────────────────────────┘
│                             │  │
│ [Start All] [Stop All]      │  │            ┌─────────────────────────┐
└─────────────────────────────┘  │            │ Student 3 (192.168.1.12)│
                                 └───HTTP────▶│ • server_agent.py       │
                                              │ • main.py (face)        │
                                              │ • yolo_detection.py     │
                                              └─────────────────────────┘
```

## 🚀 Quick Start

### **STUDENT PCs (Run on each of the 3 student machines):**

1. **Connect phone via USB** with CAMO app running (for desk camera)

2. **Start the server agent:**
   ```powershell
   python server_agent.py
   ```
   
3. **Note the displayed IP address** (e.g., `192.168.1.10`, `192.168.1.11`, `192.168.1.12`)

### **PROCTOR PC (Run once):**

1. **Launch the multi-student dashboard:**
   ```powershell
   python start_multi_proctor.py
   ```
   
2. **In the dashboard sidebar:**
   - Enter Student 1 IP → Click "Connect"
   - Enter Student 2 IP → Click "Connect"
   - Enter Student 3 IP → Click "Connect"
   
3. **Start monitoring:**
   - Click "🚀 Start All" to begin monitoring all students
   - OR click individual "▶️ Start" buttons for each student

## 📊 Dashboard Features

### **Summary Bar (Top)**
- **👥 X/3 Connected:** Number of students connected
- **▶️ X Monitoring:** Number of active monitoring sessions
- **⚠️ X Total Violations:** Aggregate violations across all students
- **🚨 X Flagged:** Number of students flagged for cheating

### **Student Cards (3-Column Grid)**

Each student card shows:

#### **Status Box (Color-Coded)**
- 🟢 **Green (NORMAL)**: `is_cheating = False`, normal behavior
- 🔴 **Red (CHEATING)**: `is_cheating = True`, cheating detected
- 🔵 **Blue (IDLE)**: Connected but not monitoring
- ⚫ **Gray (DISCONNECTED)**: Not connected

#### **Quick Metrics**
- Total Violations
- Face Violations
- Cheating Confidence %
- Object Violations

#### **Expandable Details** (Click "📊 View Details")
- **Decision Engine**: Cheating reason and confidence breakdown
- **Face Tracking**: Gaze direction, head pose, eye velocity, flagged status
- **Object Detection**: Detected objects, prohibited items, inference time
- **Recent Events**: Last 10 events with timestamps

### **Sidebar Controls**

#### **Per-Student Controls**
- **IP Input**: Enter student's IP address
- **🔗 Connect / 🔴 Disconnect**: Individual connection control
- **▶️ Start / ⏹️ Stop**: Individual monitoring control
- **Status Indicator**: 🟢 Connected / 🔴 Not Connected

#### **Batch Operations**
- **🔗 Connect All**: Connect to all 3 students at once
- **🔴 Disconnect All**: Disconnect all students
- **🚀 Start All**: Start monitoring all connected students
- **🛑 Stop All**: Stop monitoring all students

#### **Settings**
- **🔊 Sound Alerts**: Enable/disable audio alerts for cheating
- **🔄 Auto Refresh**: Toggle automatic dashboard updates (default: ON)

## 🔧 Configuration

### **IP Persistence**

Student IP addresses are automatically saved to `student_ips.json` and restored when the dashboard restarts. You don't need to re-enter IPs every time.

```json
{
  "1": "192.168.1.10",
  "2": "192.168.1.11",
  "3": "192.168.1.12"
}
```

### **Polling Configuration**

The dashboard polls all students **every 1 second** when monitoring is active. This is done concurrently using threading, so all 3 students are polled simultaneously without blocking.

## 📝 Usage Workflow

### **Before Exam:**

1. **Set up all 3 student PCs:**
   - Connect phone with CAMO
   - Run `python server_agent.py`
   - Note IP addresses

2. **Set up proctor PC:**
   - Run `python start_multi_proctor.py`
   - Enter all 3 student IPs
   - Click "Connect All"

### **During Exam:**

1. **Start monitoring:**
   - Click "🚀 Start All"
   - All students begin monitoring simultaneously

2. **Monitor in real-time:**
   - Watch color-coded status boxes
   - Check violation counts
   - Expand cards for detailed info
   - Listen for sound alerts (if enabled)

3. **Individual control:**
   - Pause specific students if needed
   - Stop and restart individual sessions
   - Disconnect problematic connections

### **After Exam:**

1. **Stop monitoring:**
   - Click "🛑 Stop All"
   - Or click individual "⏹️ Stop" buttons

2. **Review logs:**
   - Each student's logs saved on their PC
   - Located in `logs/` folder
   - Timestamped CSV and JSON files

## 🔒 Network & Security

### **Firewall Rules (Student PCs)**

Each student PC needs these firewall rules:

```powershell
# Run as Administrator on each student PC
New-NetFirewallRule -DisplayName "CheatGuard API" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "CheatGuard Logs" -Direction Inbound -LocalPort 9020,9021 -Protocol TCP -Action Allow
```

### **Network Requirements**
- All PCs must be on the **same local network**
- No internet required (everything runs locally)
- Uses ports: **5000** (API), **9020** (face logs), **9021** (object logs)

## 🐛 Troubleshooting

### **"Cannot connect to Student X"**

1. Check student PC has `server_agent.py` running
2. Verify IP address is correct
3. Check firewall rules on student PC
4. Ping the student PC: `ping 192.168.1.X`

### **"Status not updating"**

1. Check "🔄 Auto Refresh" is enabled
2. Verify monitoring is started (not just connected)
3. Check student PC terminals for errors
4. Try disconnecting and reconnecting

### **"All students show Disconnected"**

1. Check network connectivity
2. Verify all student PCs have `server_agent.py` running
3. Check firewall isn't blocking connections
4. Try "Connect All" button again

### **"High CPU usage on proctor PC"**

1. Disable "Auto Refresh" temporarily
2. Reduce number of connected students
3. Check for network latency issues
4. Close unnecessary browser tabs

## 📈 Performance

### **Tested Configuration**
- **Students**: 3 simultaneous
- **Polling Rate**: 1 second per student
- **Network**: 100 Mbps LAN
- **Proctor PC**: 8GB RAM, quad-core CPU
- **Student PCs**: 4GB RAM minimum

### **Resource Usage (Per Student)**
- **Network**: ~1 KB/s per student (status updates)
- **CPU**: <5% on proctor PC (polling + UI)
- **Memory**: ~100MB total for dashboard

## 🎓 Comparison: Single vs Multi-Student

| Feature | Single Student Dashboard | Multi-Student Dashboard |
|---------|-------------------------|------------------------|
| Students | 1 | 3 |
| Layout | Full screen details | 3-column grid |
| Controls | Single START/STOP | Individual + Batch |
| Status | Large display | Compact cards |
| Details | Always visible | Expandable |
| IP Storage | No | Yes (JSON) |
| Concurrent Polling | N/A | Threading |
| Use Case | Testing, single exam | Real proctoring |

## 🔄 Migration from Single-Student

The multi-student dashboard is **completely separate** from the original dashboard. Both can coexist:

- **Original**: `proctor_dashboard.py` - For single student, testing
- **New**: `multi_student_dashboard.py` - For 3 students, real exams

**No changes needed** to student-side code (`server_agent.py`, `main.py`, `yolo_detection.py`). The same student setup works with both dashboards.

## 🎯 Best Practices

1. **Test Before Exam:**
   - Connect all students 15 minutes early
   - Verify all cameras working
   - Check status updates flowing

2. **Monitor Actively:**
   - Keep dashboard visible during exam
   - Enable sound alerts
   - Check summary bar regularly

3. **Handle Issues Quickly:**
   - Use individual controls for problem students
   - Don't disconnect all if one fails
   - Keep monitoring logs for review

4. **Network Stability:**
   - Use wired connections when possible
   - Avoid WiFi congestion
   - Test network bandwidth beforehand

## 📞 Support

For issues or questions:
1. Check logs in each student's `logs/` folder
2. Review terminal output on student PCs
3. Test connection with single-student dashboard first
4. Check GitHub issues for known problems

## ✅ System Validation

Before starting an exam, validate:

- [ ] All 3 student PCs running `server_agent.py`
- [ ] All student IPs entered and connected
- [ ] All students showing "🟢 Connected"
- [ ] "🚀 Start All" successfully started monitoring
- [ ] Status boxes updating every second
- [ ] Summary bar shows "3/3 Connected"
- [ ] All cameras (face + desk) working
- [ ] No error messages in terminals

---

**Ready to monitor!** 🚀 Click "🚀 Start All" and let CheatGuard watch over your exam!
