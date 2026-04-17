# 📌 Project Overview

This repository contains an AI-powered surveillance system designed to monitor a defined Region of Interest (ROI), detect people using YOLOv8, track them with ByteTrack, analyze suspicious behavior, and generate alerts with evidence capture.

The system is built in Python and supports webcam/IP stream input, real-time detection and tracking, intrusion/loitering detection, email alerts, and evidence storage.

# 📂 Folder Structure

ROI_SAS/
│── .gitignore
│── .gitattributes
│── output-1.mp4
│── PRP_GF_ MAIN _ENT_LOBBY_4_PRP 1_PRP G_20260326075000_20260326082203_5443416.mp4
│── TESTING_INPUT.mp4
│── venv/
│── project/
│   │── alert.wav
│   │── behavior.py
│   │── camera.py
│   │── config.json
│   │── detection.py
│   │── email_alert.py
│   │── evidence.py
│   │── logger.py
│   │── main.py
│   │── README.md
│   │── REPORT.md
│   │── requirements.txt
│   │── roi.py
│   │── tracking.py
│   │── ui_app.py
│   │── video_info.py
│   │── yolov8n.engine
│   │── yolov8n.onnx
│   │── yolov8s.pt
│   │── yolov8m.pt
│   │── evidence/
│   │── logs/

Note: `venv/` is the local Python virtual environment used by this project and should be kept out of Git version control.

# 🧠 Module Explanation

## ui_app.py
- Role: UI / frontend
- Handles: PyQt5 user interface, video display, ROI selection, start/stop controls, live alert logging, and event-driven email/evidence handling
- Notes: Provides a graphical workflow for users to start surveillance, draw ROI points, and view detection status.

## detection.py
- Role: AI detection
- Handles: YOLOv8 model loading and inference
- Notes: Uses `ultralytics.YOLO` to detect persons only, converting results into `supervision` detections.

## tracking.py
- Role: Tracking
- Handles: ByteTrack tracking and ID assignment/consistency
- Notes: Wraps `supervision.ByteTrack`, stabilizes IDs across occlusions, smooths bounding boxes, and manages track lifecycle.

## behavior.py
- Role: Behavior analysis
- Handles: intrusion and loitering detection
- Notes: Uses ROI membership and dwell time to produce `intrusion` and `loitering` events, with duplicate suppression and exit stability.

## camera.py
- Role: Input system
- Handles: webcam or IP stream capture
- Notes: Reads frames from a video source, supports threaded live streams, reconnects on failure, and returns frames for processing.

## email_alert.py
- Role: Notification system
- Handles: sending email alerts with attachments
- Notes: Sends SMTP email alerts with evidence image attachments and supports Gmail app-password authentication.

## evidence.py
- Role: Evidence storage
- Handles: saving annotated images for alert events
- Notes: Writes evidence photos under `evidence/<event_type>/` with ROI overlay, timestamp, and event label.

## config.json
- Role: Configuration
- Stores thresholds, ROI, email settings, input mode, source paths, evidence/log directories, and display options
- Notes: Central configuration file used by all runtime modules.

## logger.py
- Role: Event logging
- Handles: writing event records to `logs/events.log`
- Notes: Provides a simple append-based log for alerts and detections.

## main.py
- Role: Orchestration
- Handles: application startup, module initialization, main processing loop, and alert coordination
- Notes: Coordinates camera input, ROI selection, detection thread, tracking, behavior analysis, alert cooldowns, and display.

## roi.py
- Role: ROI management
- Handles: ROI selection, saving, and loading
- Notes: Provides interactive polygon ROI creation on a video frame and persisting ROI data to `config.json`.

## video_info.py
- Role: Video analysis utility
- Handles: basic video metadata reporting and playback diagnostics
- Notes: Provides a utility to inspect stream/frame properties and display live FPS/speed information.

# 🔄 System Workflow

1. Camera captures frame from the configured source.
2. Frame is passed to the detector for YOLOv8-based person detection.
3. Detections are sent to the tracker for ByteTrack-based ID assignment.
4. Tracking output is analyzed to determine ROI entry, exit, and duration.
5. ROI filtering is applied to ensure alerts are generated only inside the selected area.
6. Alerts are generated for intrusion and loitering events.
7. UI displays annotated results with bounding boxes, IDs, FPS, and status.
8. Evidence images are stored and email alerts are sent when configured.

# ⚙️ Technologies Used

- Python
- PyQt5
- OpenCV
- YOLOv8
- TensorRT
- Supervision (ByteTrack)
- SMTP email via `smtplib`

# 🧪 Virtual Environment (venv) Analysis

## venv/
- Role: Isolated Python environment for dependency management
- Purpose:
  - Keeps project dependencies separate from the global Python installation
  - Ensures reproducibility across systems

## venv Folder Structure

venv/
│── Include/
│── Lib/
│   │── site-packages/
│── Scripts/
│── pyvenv.cfg
│── share/

## Key Components Inside venv:

### Scripts/
- Contains the Python executable and activation scripts for Windows
- Used to activate the virtual environment before running the project

### Lib/site-packages/
- Contains all installed Python libraries used by this project
- Expected packages include:
  - `ultralytics` (YOLOv8)
  - `opencv-python`
  - `supervision`
  - `torch`
  - `PyQt5`
  - `numpy`
  - `pillow`

### pyvenv.cfg
- Stores environment metadata and configuration
- Records the Python interpreter path and base environment details

# ⚠️ IMPORTANT NOTES ABOUT VENV

- `venv/` is VERY LARGE and can be hundreds of MBs.
- It should NOT be uploaded to GitHub.
- It is already excluded with `.gitignore` using:

```text
venv/
```

# 📦 Dependency Management

- Dependencies are listed in `project/requirements.txt`.
- To recreate the environment:

```bash
pip install -r project/requirements.txt
```

# 🧠 BEST PRACTICE

- Use `venv` for isolation.
- Never commit `venv` to the repository.
- Share only `requirements.txt` for dependency reproduction.

# 🚀 Key Features

- Real-time human detection
- ROI-based monitoring
- Intrusion detection
- Loitering detection
- Email alert system
- Evidence capture
- High FPS GPU acceleration when available

# 📌 Notes

- Do NOT modify any code while generating this documentation.
- This file is intended for clean architectural overview and README-style presentation.
- Keep explanations simple, professional, and suitable for slide decks or GitHub documentation.
- The system is modular and can be extended with additional sensors, models, or alert channels.

---

## Summary

This repository implements an AI surveillance solution that uses a configurable ROI to watch a target area, detects people via YOLOv8, tracks them with ByteTrack, analyzes behavior for trespassing and loitering, and routes alerts through evidence capture and email notifications.
