import cv2
import json
import threading
import time


class Camera:
    def __init__(self, config_path='config.json'):
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.input_mode = config.get('input_mode', 'file')

        # Store source for reconnection
        self.source = config['video_path'] if self.input_mode == 'file' else config['webcam_url']

        if self.input_mode == 'file':
            self.cap = cv2.VideoCapture(self.source)
            self.threaded = False

        else:
            self.cap = cv2.VideoCapture(self.source)
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
            # Check if camera is still open
            if not self.cap.isOpened():
                print("⚠️ Camera disconnected. Attempting to reconnect...")
                time.sleep(1)
                try:
                    self.cap.open(self.source)
                    if not self.cap.isOpened():
                        print("⚠️ Reconnection failed, retrying...")
                    continue
                except Exception as e:
                    print(f"⚠️ Reconnection error: {e}")
                    time.sleep(1)
                    continue

            # Safely read frame with error handling
            try:
                ret, frame = self.cap.read()
            except Exception as e:
                print(f"⚠️ Camera read error: {e}")
                time.sleep(0.5)
                continue

            # Handle failed frames
            if not ret or frame is None:
                print("⚠️ Frame not received, retrying...")
                time.sleep(0.1)
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
            try:
                return self.cap.read()
            except Exception as e:
                print(f"⚠️ Camera read error: {e}")
                return False, None

    def release(self):
        if self.threaded:
            self.running = False
        self.cap.release()