import os
import cv2
import time
import numpy as np

def save_evidence(frame, event_type, track_id, roi, analyzer):
    """
    Save evidence image with:
    ✅ ROI
    ✅ Event label
    ✅ Timestamp (NEW)
    """

    # Create directory
    folder = f"evidence/{event_type}"
    os.makedirs(folder, exist_ok=True)

    timestamp = int(time.time())
    filename = f"{folder}/id{track_id}_{timestamp}.jpg"

    # 🔥 DRAW ROI
    cv2.polylines(
        frame,
        [roi.astype(np.int32)],
        isClosed=True,
        color=(0, 255, 0),
        thickness=2
    )

    # 🔥 EVENT LABEL
    px, py = roi[0]

    cv2.putText(
        frame,
        f"{event_type.upper()} ID {track_id}",
        (int(px), int(py) - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2
    )

    # 🔥 ADD TIMESTAMP (THIS IS YOUR MISSING PART)
    readable_time = time.strftime("%Y-%m-%d %H:%M:%S")

    cv2.putText(
        frame,
        readable_time,
        (10, 30),   # top-left corner
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    # 🔥 SAVE IMAGE
    cv2.imwrite(filename, frame)

    return filename