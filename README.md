# 🚀 ROI-Based Intelligent Surveillance System

## 📌 Overview
This project is an AI-powered surveillance system that monitors a defined Region of Interest (ROI), detects people using YOLOv8, tracks them with ByteTrack, and analyzes behavior for intrusion and loitering.

It supports real-time webcam/IP stream input, alert generation, email notifications, and evidence storage.

---

## 🎯 Features
- ✅ YOLOv8 + ByteTrack tracking
- ✅ ROI-based intrusion detection
- ✅ Loitering detection
- ✅ Email alerts with evidence
- ✅ Real-time UI (PyQt5)
- ✅ High FPS (GPU + TensorRT)

---

## 🧠 Tech Stack
- Python
- OpenCV
- YOLOv8 (Ultralytics)
- TensorRT (optional)
- ByteTrack (Supervision)
- PyQt5

---

## ⚙️ Installation

### 1. Clone the repository
git clone <https://github.com/PUGALENTHI-K-7/ROI-Based-Intelligent-Surveillance-and-Alert-System-WITH-UI-PyQt5-Python-Qt-Framework-.git>
cd ROI_SAS/project


### 2. Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate # Windows


### 3. Install dependencies
pip install -r requirements.txt


---

## ▶️ Run Project

### Run main system:
python main.py


### Run UI version:
python ui_app.py


---

## 📂 Project Structure
ROI_SAS/
│── project/
│ │── ui_app.py
│ │── main.py
│ │── detection.py
│ │── tracking.py
│ │── behavior.py
│ │── camera.py
│ │── email_alert.py
│ │── evidence.py
│ │── config.json
│ │── requirements.txt
│ │── yolov8n.engine
│ │── yolov8n.pt
│ │── evidence/
│ │── logs/


---

## 🧪 Model Notes

- `yolov8n.engine` → TensorRT optimized (GPU specific)
- `yolov8n.pt` → Portable fallback (recommended for other systems)

---

## ⚠️ Important Notes

- Do NOT upload `venv/` to GitHub
- Use `requirements.txt` to recreate environment
- TensorRT engine may not work on all devices
- Use `.pt` model for compatibility

---

## 🚀 Future Improvements
- Web dashboard (instead of PyQt)
- Multi-camera support
- Cloud alert system
- Mobile notifications

---

## 📌 Author
AI Surveillance Project – Final Year System
