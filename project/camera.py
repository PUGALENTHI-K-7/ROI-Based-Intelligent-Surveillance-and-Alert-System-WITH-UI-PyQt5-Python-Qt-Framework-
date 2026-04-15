import cv2
import json
import threading
import time


class Camera:
    def __init__(self, config_path='config.json'):
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.input_mode = config.get('input_mode', 'file')

        if self.input_mode == 'file':
            self.cap = cv2.VideoCapture(config['video_path'])
            self.threaded = False

        else:
            self.cap = cv2.VideoCapture(config['webcam_url'])
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self.threaded = True
            self.frame = None
            self.ret = False
            self.running = True
            self.lock = threading.Lock()

            self.thread = threading.Thread(target=self.update, daemon=True)
            self.thread.start()

        if not self.cap.isOpened():
            raise ValueError("Cannot open video source")

        print(f"[Camera] Initialized ({self.input_mode})")

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            with self.lock:
                self.ret = ret
                self.frame = frame

    def get_frame(self):
        if self.threaded:
            while self.frame is None:
                time.sleep(0.01)

            with self.lock:
                return self.ret, self.frame.copy()
        else:
            return self.cap.read()

    def release(self):
        if self.threaded:
            self.running = False
        self.cap.release()