import cv2
import json
import os
import numpy as np
import time

def load_roi(config_path='config.json'):
    if not os.path.exists(config_path):
        return None

    with open(config_path, 'r') as f:
        config = json.load(f)

    roi = config.get('roi_polygon')

    if roi is None or len(roi) < 3:
        return None

    return np.array(roi, dtype=np.int32)


def save_roi(roi, config_path='config.json'):
    with open(config_path, 'r') as f:
        config = json.load(f)

    config['roi_polygon'] = roi.tolist()

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def select_roi(camera):
    print("👉 Click points to draw ROI polygon")
    print("👉 Press ENTER to finish | Press 'c' to cancel")

    # 🔥 WAIT FOR FRAME (CRITICAL FIX)
    frame = None
    for _ in range(100):  # try for ~5 seconds
        ret, frame = camera.get_frame()
        if ret and frame is not None:
            break
        time.sleep(0.05)

    if frame is None:
        raise ValueError("Cannot read frame for ROI")

    clone = frame.copy()
    points = []

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))

    window_name = "Select ROI"

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # 🔥 AUTO SCALE WINDOW (FIX FREEZE / BLANK ISSUE)
    screen_w, screen_h = 1280, 720
    h, w = frame.shape[:2]

    scale = min(screen_w / w, screen_h / h)
    new_w, new_h = int(w * scale), int(h * scale)

    cv2.resizeWindow(window_name, new_w, new_h)

    cv2.setMouseCallback(window_name, mouse_callback)

    while True:
        temp = clone.copy()

        # draw points
        for p in points:
            cv2.circle(temp, p, 5, (0, 0, 255), -1)

        # draw lines
        if len(points) > 1:
            cv2.polylines(temp, [np.array(points)], False, (0, 255, 0), 2)

        if len(points) > 2:
            cv2.line(temp, points[-1], points[0], (255, 0, 0), 1)

        cv2.imshow(window_name, temp)

        key = cv2.waitKey(1) & 0xFF

        if key == 13:  # ENTER
            break
        elif key == ord('c'):
            cv2.destroyAllWindows()
            raise ValueError("ROI selection cancelled")

    cv2.destroyAllWindows()

    if len(points) < 3:
        raise ValueError("Need at least 3 points")

    roi = np.array(points, dtype=np.int32)

    print("✅ Polygon ROI Selected:", roi.tolist())

    return roi