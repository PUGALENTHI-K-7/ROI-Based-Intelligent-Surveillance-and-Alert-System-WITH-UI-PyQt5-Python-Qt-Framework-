from ultralytics import YOLO
import supervision as sv
import torch


class Detector:
    def __init__(self, model_path='yolov8n.engine'):
        self.model = YOLO(model_path)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔥 Detector running on: {self.device}")

    def detect(self, frame):
        results = self.model(
            frame,
            device=self.device,
            verbose=False,
            classes=[0],
            imgsz=960,
            conf=0.5,
            iou=0.5
        )[0]

        return sv.Detections.from_ultralytics(results)