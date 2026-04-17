import time
import cv2
import supervision as sv
import numpy as np
from typing import Dict, List, Tuple, Optional

class BehaviorAnalyzer:
    def __init__(self, roi_polygon: np.ndarray, loiter_threshold: float = 20.0):  # 🔥 increased
        self.roi_polygon = roi_polygon
        self.loiter_threshold = loiter_threshold

        self.id_enter_time: Dict[int, float] = {}
        self.in_roi: Dict[int, bool] = {}
        self.reported_loitering = set()

        # 🔥 DUPLICATE CONTROL
        self.recent_intrusions = []
        self.COOLDOWN_DIST = 60
        self.COOLDOWN_TIME = 5

        # 🔥 EXIT STABILITY (CRITICAL FIX)
        self.exit_buffer = {}
        self.EXIT_DELAY = 2  # seconds

    # 🔥 MULTI-POINT CHECK
    def is_bbox_inside_roi(self, bbox):
        x1, y1, x2, y2 = bbox

        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        # Only center point must be inside ROI
        return cv2.pointPolygonTest(self.roi_polygon, (cx, cy), False) >= 0

    # 🔥 OVERLAP CHECK
    def bbox_roi_overlap(self, bbox, frame_shape):
        x1, y1, x2, y2 = map(int, bbox)
        h, w = frame_shape[:2]

        mask_roi = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask_roi, [self.roi_polygon], 255)

        mask_box = np.zeros((h, w), dtype=np.uint8)
        cv2.rectangle(mask_box, (x1, y1), (x2, y2), 255, -1)

        intersection = cv2.bitwise_and(mask_roi, mask_box)

        overlap_pixels = cv2.countNonZero(intersection)
        box_pixels = max((x2 - x1) * (y2 - y1), 1)

        overlap_ratio = overlap_pixels / box_pixels

        return overlap_ratio > 0.3

    # 🔥 DUPLICATE CHECK
    def is_duplicate_intrusion(self, cx, cy):
        current_time = time.time()

        for (px, py, t) in self.recent_intrusions:
            dist = np.hypot(cx - px, cy - py)

            if dist < self.COOLDOWN_DIST and (current_time - t < self.COOLDOWN_TIME):
                return True

        return False

    def update(self, tracks: sv.Detections, frame_shape=None) -> List[Tuple[str, int, float]]:
        events = []

        if tracks is None or len(tracks) == 0:
            return events

        for track_id in tracks.tracker_id:

            mask = tracks.tracker_id == track_id
            if not mask.any():
                continue

            bbox = tracks.xyxy[mask][0]

            # 🔥 ROI LOGIC
            is_in_roi = self.is_bbox_inside_roi(bbox)

            if frame_shape is not None:
                is_in_roi = is_in_roi or self.bbox_roi_overlap(bbox, frame_shape)

            # 🔥 INIT STATE
            if track_id not in self.in_roi:
                self.in_roi[track_id] = False

            # 🔥 STATE CHANGE
            if self.in_roi[track_id] != is_in_roi:

                # =========================
                # ✅ ENTER ROI
                # =========================
                if is_in_roi:
                    cx = (bbox[0] + bbox[2]) / 2
                    cy = (bbox[1] + bbox[3]) / 2

                    # 🔥 RESET EXIT BUFFER
                    if track_id in self.exit_buffer:
                        del self.exit_buffer[track_id]

                    if not self.is_duplicate_intrusion(cx, cy):

                        self.recent_intrusions.append((cx, cy, time.time()))

                        if len(self.recent_intrusions) > 50:
                            self.recent_intrusions = self.recent_intrusions[-50:]

                        self.id_enter_time[track_id] = time.time()
                        self.in_roi[track_id] = True

                        events.append(('intrusion', track_id, time.time()))

                # =========================
                # ❌ EXIT ROI (STABLE)
                # =========================
                else:
                    current_time = time.time()

                    # first time detected outside
                    if track_id not in self.exit_buffer:
                        self.exit_buffer[track_id] = current_time

                    # confirm exit after delay
                    elif current_time - self.exit_buffer[track_id] > self.EXIT_DELAY:

                        self.in_roi[track_id] = False

                        if track_id in self.id_enter_time:
                            del self.id_enter_time[track_id]

                        if track_id in self.reported_loitering:
                            self.reported_loitering.remove(track_id)

                        del self.exit_buffer[track_id]

        # 🔥 LOITERING
        now = time.time()

        for track_id in list(self.id_enter_time.keys()):
            if self.in_roi.get(track_id, False):

                loiter_time = now - self.id_enter_time[track_id]

                if loiter_time > self.loiter_threshold:

                    if track_id not in self.reported_loitering:
                        events.append(('loitering', track_id, now))
                        self.reported_loitering.add(track_id)

        return events

    def get_loiter_time(self, track_id: int) -> Optional[float]:
        if track_id in self.id_enter_time:
            return time.time() - self.id_enter_time[track_id]
        return None


# 🔥 FACTORY
import json

def get_analyzer(roi_polygon, config_path='config.json'):
    with open(config_path, 'r') as f:
        config = json.load(f)

    threshold = config.get('loiter_threshold', 10.0)

    return BehaviorAnalyzer(roi_polygon, threshold)