import cv2
import json
import time
import threading
import winsound

from camera import Camera
from roi import select_roi, save_roi
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


# 🔥 DETECTION THREAD
def detection_worker(detector, tracker):
    global latest_frame, latest_tracks

    while True:
        if latest_frame is None:
            continue

        with frame_lock:
            frame = latest_frame.copy()

        detections = detector.detect(frame)

        if detections is not None and len(detections) > 0:
            tracks = tracker.update(detections, frame)

            with track_lock:
                latest_tracks = tracks


def main():
    global latest_frame, latest_tracks

    config_path = 'config.json'

    with open(config_path, 'r') as f:
        config = json.load(f)

    camera = Camera(config_path)
    time.sleep(2)

    # 🔥 MODE DETECTION
    is_webcam = camera.input_mode != "file"

    roi = select_roi(camera)
    save_roi(roi, config_path)

    detector = Detector()
    tracker = Tracker()

    analyzer = get_analyzer(roi.astype(int), config_path)

    cv2.namedWindow("Intelligent Surveillance System", cv2.WINDOW_NORMAL)

    # 🔥 ALERT CONTROL
    last_alert_time = {}
    ALERT_COOLDOWN = 10
    GLOBAL_COOLDOWN = 5
    last_global_alert = 0
    sent_ids = set()

    # 🔥 START DETECTION THREAD
    threading.Thread(
        target=detection_worker,
        args=(detector, tracker),
        daemon=True
    ).start()

    prev_time = time.time()
    fps = 0

    print("🚀 System started. Press 'q' to quit.")

    while True:

        ret, frame = camera.get_frame()
        if not ret:
            continue

        # 🔥 UPDATE SHARED FRAME
        with frame_lock:
            latest_frame = frame.copy()

        annotated = frame.copy()
        cv2.polylines(annotated, [roi], True, (0, 0, 255), 2)

        # 🔥 GET TRACKS
        with track_lock:
            tracks = latest_tracks

        if tracks is not None and len(tracks) > 0:

            events = analyzer.update(tracks, frame.shape)

            for event_type, track_id, ts in events:

                event_key = f"{event_type}_{track_id}"
                current_time = time.time()

                if event_key in sent_ids:
                    continue

                if current_time - last_global_alert < GLOBAL_COOLDOWN:
                    continue

                if event_key not in last_alert_time or (
                    current_time - last_alert_time[event_key] > ALERT_COOLDOWN
                ):

                    sent_ids.add(event_key)
                    last_alert_time[event_key] = current_time
                    last_global_alert = current_time

                    threading.Thread(target=play_alert_sound, daemon=True).start()

                    threading.Thread(
                        target=handle_alert,
                        args=(frame.copy(), event_type, track_id, roi, analyzer, config_path),
                        daemon=True
                    ).start()

            # 🔥 DRAW BOXES
            for i, bbox in enumerate(tracks.xyxy):
                x1, y1, x2, y2 = map(int, bbox)
                tid = tracks.tracker_id[i]

                cv2.rectangle(annotated, (x1, y1), (x2, y2),
                              (0, 255, 0), 2, cv2.LINE_AA)

                cv2.putText(
                    annotated,
                    f"ID {tid}",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 0),
                    2,
                    cv2.LINE_AA
                )

        # 🔥 FPS CALCULATION
        current_time = time.time()
        fps = 0.9 * fps + 0.1 * (1 / (current_time - prev_time))
        prev_time = current_time

        # 🔥 UI SETTINGS (FINAL FIX)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.9   # ~20px look
        thickness = 2

        # ✅ FPS (for both modes)
        cv2.putText(
            annotated,
            f"FPS: {int(fps)}",
            (20, 60),   # moved down (no overlap)
            font,
            font_scale,
            (0, 255, 0),
            thickness,
            cv2.LINE_AA
        )

        # ✅ ONLY WEBCAM → TIMESTAMP
        if is_webcam:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            cv2.putText(
                annotated,
                timestamp,
                (20, 100),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )

        cv2.imshow("Intelligent Surveillance System", annotated)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()


def handle_alert(frame, event_type, track_id, roi, analyzer, config_path):
    try:
        evidence_path = save_evidence(frame, event_type, track_id, roi, analyzer)
        send_alert(event_type, track_id, evidence_path, config_path)
    except Exception as e:
        print(f"Alert error: {e}")


if __name__ == "__main__":
    main()