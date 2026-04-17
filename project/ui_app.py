import sys
import cv2
import json
import time
import threading
import winsound
import numpy as np

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QListWidget, QFrame, QSizePolicy
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject

from camera import Camera
from detection import Detector
from tracking import Tracker
from behavior import get_analyzer
from evidence import save_evidence
from email_alert import send_alert

# 🔥 GLOBAL SHARED DATA
latest_frame = None
latest_tracks = None

frame_lock = threading.Lock()
track_lock = threading.Lock()


def play_alert_sound():
    try:
        winsound.Beep(1000, 300)
    except:
        pass


def handle_alert(frame, event_type, track_id, roi, analyzer, config_path):
    try:
        evidence_path = save_evidence(frame, event_type, track_id, roi, analyzer)
        send_alert(event_type, track_id, evidence_path, config_path)
    except Exception as e:
        print(f"Alert error: {e}")


class VideoLabelSignals(QObject):
    """Signals for video label mouse events"""
    mouse_clicked = pyqtSignal(int, int)


class ClickableVideoLabel(QLabel):
    """Custom QLabel that captures mouse clicks for ROI selection with proper coordinate mapping"""
    def __init__(self):
        super().__init__()
        self.signals = VideoLabelSignals()
        self.original_width = 0
        self.original_height = 0
        self.display_pixmap = None

    def set_frame_dimensions(self, original_w, original_h):
        """Store original frame dimensions for coordinate mapping"""
        self.original_width = original_w
        self.original_height = original_h

    def setPixmap(self, pixmap):
        """Override setPixmap to track the displayed pixmap for accurate coordinate mapping"""
        super().setPixmap(pixmap)
        self.display_pixmap = pixmap

    def mousePressEvent(self, event):
        """
        Handle mouse click - convert from QLabel display coordinates to original frame coordinates.
        
        Coordinate transformation:
        1. QLabel click → pixmap offset (account for letterboxing)
        2. Pixmap coords → frame coords (account for scaling)
        """
        if self.original_width == 0 or self.original_height == 0 or self.display_pixmap is None:
            return

        # Get click position in QLabel coordinates
        click_x = event.x()
        click_y = event.y()

        # Get the actual displayed pixmap dimensions (after aspect ratio scaling)
        pixmap_w = self.display_pixmap.width()
        pixmap_h = self.display_pixmap.height()

        # Calculate letterbox offsets (QLabel centers the pixmap with black padding)
        label_w = self.width()
        label_h = self.height()
        offset_x = (label_w - pixmap_w) // 2
        offset_y = (label_h - pixmap_h) // 2

        # Convert from QLabel coordinates to pixmap coordinates
        display_x = click_x - offset_x
        display_y = click_y - offset_y

        # Reject clicks in black padding area
        if display_x < 0 or display_y < 0 or display_x >= pixmap_w or display_y >= pixmap_h:
            return  # Click in letterbox padding, ignore

        # Map from pixmap coordinates to original frame coordinates
        scale_x = self.original_width / pixmap_w
        scale_y = self.original_height / pixmap_h

        real_x = int(display_x * scale_x)
        real_y = int(display_y * scale_y)

        # Emit signal with frame coordinates
        self.signals.mouse_clicked.emit(real_x, real_y)


class SurveillanceUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Intelligent Surveillance System")
        self.setGeometry(100, 100, 1200, 900)
        self.setStyleSheet("background-color: #2b2b2b; color: white;")

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # TOP: Title
        title_label = QLabel("Intelligent Surveillance System")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setStyleSheet("color: #00ff00; margin-bottom: 10px;")
        layout.addWidget(title_label, 1)

        # MIDDLE: Video display (using custom clickable label)
        self.video_label = ClickableVideoLabel()
        self.video_label.setMinimumSize(800, 500)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; border: 2px solid #444;")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.signals.mouse_clicked.connect(self.on_video_click)
        layout.addWidget(self.video_label, 6)

        # BELOW VIDEO: Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        self.start_btn = QPushButton("Start")
        self.start_btn.setFont(QFont("Arial", 12))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: 2px solid #555;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.start_btn.clicked.connect(self.start_surveillance)
        controls_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFont(QFont("Arial", 12))
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: 2px solid #555;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_surveillance)
        controls_layout.addWidget(self.stop_btn)

        self.roi_btn = QPushButton("Set ROI")
        self.roi_btn.setFont(QFont("Arial", 12))
        self.roi_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: 2px solid #555;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.roi_btn.clicked.connect(self.set_roi)
        controls_layout.addWidget(self.roi_btn)

        # Finish ROI button (hidden initially)
        self.finish_roi_btn = QPushButton("Finish ROI (Press ENTER)")
        self.finish_roi_btn.setFont(QFont("Arial", 12))
        self.finish_roi_btn.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                color: white;
                border: 2px solid #00ff00;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #00dd00;
            }
        """)
        self.finish_roi_btn.clicked.connect(self.finish_roi_selection)
        self.finish_roi_btn.setVisible(False)
        controls_layout.addWidget(self.finish_roi_btn)

        layout.addLayout(controls_layout, 1)

        # BOTTOM: Panels
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)

        # Alerts and Email panels (two columns)
        alerts_container = QWidget()
        alerts_container.setMinimumWidth(500)
        alerts_container_layout = QHBoxLayout(alerts_container)
        alerts_container_layout.setSpacing(15)
        alerts_container_layout.setContentsMargins(0, 0, 0, 0)

        # LEFT COLUMN: Detection Alerts
        left_column = QWidget()
        left_column_layout = QVBoxLayout(left_column)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_title = QLabel("Detection Alerts")
        left_title.setFont(QFont("Arial", 11, QFont.Bold))
        left_title.setStyleSheet("color: #00ff00;")
        left_column_layout.addWidget(left_title)
        self.alerts_list = QListWidget()
        self.alerts_list.setFont(QFont("Consolas", 10))
        self.alerts_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 2px solid #444;
                border-radius: 5px;
            }
        """)
        self.alerts_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_column_layout.addWidget(self.alerts_list)
        alerts_container_layout.addWidget(left_column, 1)

        # RIGHT COLUMN: Email Logs
        right_column = QWidget()
        right_column_layout = QVBoxLayout(right_column)
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        right_title = QLabel("Email Logs")
        right_title.setFont(QFont("Arial", 11, QFont.Bold))
        right_title.setStyleSheet("color: #00ff00;")
        right_column_layout.addWidget(right_title)
        self.email_list = QListWidget()
        self.email_list.setFont(QFont("Consolas", 10))
        self.email_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 2px solid #444;
                border-radius: 5px;
            }
        """)
        self.email_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_column_layout.addWidget(self.email_list)
        alerts_container_layout.addWidget(right_column, 1)

        bottom_layout.addWidget(alerts_container, 2)

        # Stats panel
        stats_frame = QFrame()
        stats_frame.setMinimumWidth(300)
        stats_frame.setStyleSheet("background-color: #2b2b2b; border: 2px solid #444; border-radius: 5px;")
        stats_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        self.fps_label = QLabel("FPS: <span style='color: #00ff00;'>0</span>")
        self.fps_label.setFont(QFont("Arial", 12))
        stats_layout.addWidget(self.fps_label)
        self.person_count_label = QLabel("Active persons: <span style='color: #00ff00;'>0</span>")
        self.person_count_label.setFont(QFont("Arial", 12))
        stats_layout.addWidget(self.person_count_label)
        self.alert_count_label = QLabel("Alerts: <span style='color: #00ff00;'>0</span>")
        self.alert_count_label.setFont(QFont("Arial", 12))
        stats_layout.addWidget(self.alert_count_label)
        bottom_layout.addWidget(stats_frame, 3)

        layout.addLayout(bottom_layout, 3)

        # Timer for updating UI
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(1)  # Unlimited FPS

        # Backend variables
        self.camera = None
        self.detector = None
        self.tracker = None
        self.analyzer = None
        self.roi = None
        self.running = False
        self.alert_count = 0
        self.last_alert_time = {}
        self.ALERT_COOLDOWN = 10
        self.GLOBAL_COOLDOWN = 5
        self.last_global_alert = 0
        self.sent_ids = set()
        self.prev_time = time.time()
        self.fps = 0
        self.is_webcam = False

        # ROI Selection variables
        self.roi_drawing = False
        self.roi_points = []
        self.roi_frame = None

        # System state variables
        self.roi_selected = False
        self.detection_active = False

        # Start detection thread
        self.detection_thread = threading.Thread(target=self.run_detection, daemon=True)
        self.detection_thread.start()

        # Set focus to capture key events
        self.setFocus()

    def on_video_click(self, x, y):
        """Handle video label click during ROI selection"""
        if not self.roi_drawing:
            return

        self.roi_points.append((x, y))
        print(f"📍 ROI point {len(self.roi_points)}: ({x}, {y}) - Frame coords")

    def set_roi(self):
        """Enable ROI selection mode"""
        if not self.running or self.camera is None:
            print("⚠️ Start surveillance first")
            return

        if self.roi_drawing:
            print("⚠️ ROI selection already active")
            return

        self.roi_drawing = True
        self.roi_points = []
        self.finish_roi_btn.setVisible(True)
        self.roi_btn.setEnabled(False)
        print("🎯 ROI selection mode ON - click on video to add points, press ENTER to finish")

    def finish_roi_selection(self):
        """Finish ROI selection and save"""
        if not self.roi_drawing or len(self.roi_points) < 3:
            print(f"⚠️ Need at least 3 points (current: {len(self.roi_points)})")
            return

        roi = np.array(self.roi_points, dtype=np.int32)
        self.roi = roi

        # Save to config
        config_path = 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        config['roi_polygon'] = roi.tolist()
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        # Initialize detection pipeline
        self.detector = Detector()
        self.tracker = Tracker()
        self.analyzer = get_analyzer(self.roi.astype(int), config_path)
        self.roi_selected = True
        self.detection_active = True

        # Exit selection mode
        self.roi_drawing = False
        self.roi_points = []
        self.finish_roi_btn.setVisible(False)
        self.roi_btn.setEnabled(True)

        print(f"✅ ROI saved: {roi.tolist()}")
        print("🚀 Detection pipeline started!")

    def keyPressEvent(self, event):
        """Handle key presses"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.roi_drawing:
                self.finish_roi_selection()
        elif event.key() == Qt.Key_Escape:
            if self.roi_drawing:
                self.roi_drawing = False
                self.roi_points = []
                self.finish_roi_btn.setVisible(False)
                self.roi_btn.setEnabled(True)
                print("❌ ROI selection cancelled")
        super().keyPressEvent(event)

    def start_surveillance(self):
        if self.running:
            return
        config_path = 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        self.camera = Camera(config_path)
        time.sleep(2)
        self.is_webcam = self.camera.input_mode != "file"

        # Do NOT load ROI automatically - user must select it
        self.roi = None
        self.roi_selected = False
        self.detection_active = False

        # Do NOT initialize detector/tracker/analyzer yet
        self.detector = None
        self.tracker = None
        self.analyzer = None

        self.running = True
        print("🚀 Camera started - please select ROI to begin detection.")

    def stop_surveillance(self):
        self.timer.stop()  # Stop timer first to avoid thread issues
        self.running = False
        if self.camera:
            self.camera.release()
        self.timer.start(1)  # Restart timer for next surveillance start

        # Reset state
        self.roi_selected = False
        self.detection_active = False
        self.roi_drawing = False
        self.roi_points = []
        self.finish_roi_btn.setVisible(False)
        self.roi_btn.setEnabled(True)
        self.roi = None
        self.detector = None
        self.tracker = None
        self.analyzer = None

        print("🛑 Surveillance stopped.")

    def run_detection(self):
        global latest_frame, latest_tracks
        while True:
            if not self.running or not self.detection_active or latest_frame is None or self.detector is None:
                time.sleep(0.01)
                continue
            with frame_lock:
                frame = latest_frame.copy()
            detections = self.detector.detect(frame)
            if detections is not None and len(detections) > 0:
                tracks = self.tracker.update(detections, frame)
                with track_lock:
                    latest_tracks = tracks

    def update_ui(self):
        global latest_frame
        if not self.running or self.camera is None:
            return
        ret, frame = self.camera.get_frame()
        if not ret:
            return  # Safely skip if frame read fails
        # Update shared frame
        with frame_lock:
            latest_frame = frame.copy()
        annotated = frame.copy()

        # Draw existing ROI if set
        if self.roi is not None and len(self.roi) >= 3:
            cv2.polylines(annotated, [self.roi], True, (0, 0, 255), 2)

        # Draw ROI selection in progress
        if self.roi_drawing and len(self.roi_points) > 0:
            # Draw points
            for point in self.roi_points:
                cv2.circle(annotated, point, 8, (0, 255, 0), -1)
                cv2.circle(annotated, point, 10, (0, 255, 255), 2)

            # Draw lines between points
            if len(self.roi_points) > 1:
                cv2.polylines(annotated, [np.array(self.roi_points)], False, (0, 255, 0), 2)

            # Draw line from last point to first (closing polygon)
            if len(self.roi_points) > 2:
                cv2.line(annotated, self.roi_points[-1], self.roi_points[0], (255, 0, 0), 2)

            # Show instruction
            cv2.putText(annotated, f"Points: {len(self.roi_points)} - Press ENTER to finish",
                       (20, annotated.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Show message if ROI not selected
        if not self.roi_selected and not self.roi_drawing:
            cv2.putText(annotated, "Please select ROI to start detection",
                       (20, annotated.shape[0] // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3, cv2.LINE_AA)
            cv2.putText(annotated, "Please select ROI to start detection",
                       (20, annotated.shape[0] // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2, cv2.LINE_AA)

        # Get tracks and run detection only if ROI is selected
        person_count = 0
        if self.roi_selected and self.detection_active and self.detector is not None:
            with track_lock:
                tracks = latest_tracks
            if tracks is not None and len(tracks) > 0 and not self.roi_drawing:
                person_count = len(tracks)
                events = self.analyzer.update(tracks, frame.shape)
                for event_type, track_id, ts in events:
                    event_key = f"{event_type}_{track_id}"
                    current_time = time.time()
                    if event_key in self.sent_ids:
                        continue
                    if current_time - self.last_global_alert < self.GLOBAL_COOLDOWN:
                        continue
                    if event_key not in self.last_alert_time or (
                        current_time - self.last_alert_time[event_key] > self.ALERT_COOLDOWN
                    ):
                        self.sent_ids.add(event_key)
                        self.last_alert_time[event_key] = current_time
                        self.last_global_alert = current_time
                        self.alert_count += 1
                        # Add to detection alerts (LEFT panel)
                        self.alerts_list.addItem(f"{event_type} - ID {track_id}")
                        if self.alerts_list.count() > 50:
                            self.alerts_list.takeItem(0)
                        # Log to email logs (RIGHT panel)
                        self.email_list.addItem(f"✅ Email sent: {event_type} | ID {track_id}")
                        if self.email_list.count() > 50:
                            self.email_list.takeItem(0)
                        threading.Thread(target=play_alert_sound, daemon=True).start()
                        threading.Thread(
                            target=handle_alert,
                            args=(frame.copy(), event_type, track_id, self.roi, self.analyzer, 'config.json'),
                            daemon=True
                        ).start()
                # Draw boxes
                for i, bbox in enumerate(tracks.xyxy):
                    x1, y1, x2, y2 = map(int, bbox)
                    tid = tracks.tracker_id[i]
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(annotated, f"ID {tid}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
        # FPS calculation
        current_time = time.time()
        self.fps = 0.9 * self.fps + 0.1 * (1 / (current_time - self.prev_time))
        self.prev_time = current_time
        cv2.putText(annotated, f"FPS: {int(self.fps)}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
        if self.is_webcam:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(annotated, timestamp, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        # Convert to QPixmap and display
        rgb_image = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)

        # Get scaled dimensions
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.FastTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

        # Update label with frame dimensions
        self.video_label.set_frame_dimensions(w, h)
        # Update stats
        self.fps_label.setText(f"FPS: <span style='color: #00ff00;'>{int(self.fps)}</span>")
        self.person_count_label.setText(f"Active persons: <span style='color: #00ff00;'>{person_count}</span>")
        self.alert_count_label.setText(f"Alerts: <span style='color: #00ff00;'>{self.alert_count}</span>")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SurveillanceUI()
    window.show()
    sys.exit(app.exec_())