import supervision as sv
import time
import numpy as np

class Tracker:
    def __init__(self):
        self.tracker = sv.ByteTrack()

        self.id_map = {}
        self.last_positions = {}
        self.last_seen = {}

        # 🔥 FIXED VALUES
        self.max_disappear_time = 30     # was 15
        self.distance_threshold = 40     # was 80 (VERY IMPORTANT)

        # 🔥 SMOOTHER BOUNDING BOX TRACKING
        self.smooth_positions = {}
        self.smooth_factor = 0.4

        self._next_pid = 1

    def _get_center(self, bbox):
        x1, y1, x2, y2 = bbox
        return int((x1 + x2) / 2), int((y1 + y2) / 2)

    def _find_match(self, center):
        current_time = time.time()

        best_pid = None
        best_dist = float("inf")

        for pid in self.last_positions:

            if current_time - self.last_seen.get(pid, 0) > self.max_disappear_time:
                continue

            prev_center = self.last_positions[pid]
            dist = np.linalg.norm(np.array(center) - np.array(prev_center))

            if dist < self.distance_threshold and dist < best_dist:
                best_dist = dist
                best_pid = pid

        return best_pid

    def update(self, detections, frame):

        tracks = self.tracker.update_with_detections(detections)

        if tracks is None or len(tracks) == 0:
            return tracks

        current_time = time.time()
        active_bt_ids = set()

        for i, bbox in enumerate(tracks.xyxy):

            bt_id = int(tracks.tracker_id[i])
            active_bt_ids.add(bt_id)

            center = self._get_center(bbox)

            # 🔥 SMOOTH BOUNDING BOX POSITIONS
            pid_temp = self.id_map.get(bt_id)
            if pid_temp in self.smooth_positions:
                prev = self.smooth_positions[pid_temp]
                center = (
                    int(self.smooth_factor * prev[0] + (1 - self.smooth_factor) * center[0]),
                    int(self.smooth_factor * prev[1] + (1 - self.smooth_factor) * center[1])
                )

            if bt_id in self.id_map:
                pid = self.id_map[bt_id]
            else:
                pid = self._find_match(center)

                if pid is None:
                    pid = self._next_pid
                    self._next_pid += 1

                self.id_map[bt_id] = pid

            tracks.tracker_id[i] = pid

            self.last_positions[pid] = center
            self.smooth_positions[pid] = center
            self.last_seen[pid] = current_time

        self.id_map = {
            bt_id: pid for bt_id, pid in self.id_map.items()
            if bt_id in active_bt_ids
        }

        return tracks