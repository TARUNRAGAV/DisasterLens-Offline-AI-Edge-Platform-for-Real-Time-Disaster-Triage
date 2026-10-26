import cv2
import torch
from ultralytics import YOLO

class DisasterDetector:
    def __init__(self, model_path: str = "models/yolov8n.pt", conf_thresh: float = 0.45):
        # Dynamically allocate hardware acceleration if an NVIDIA GPU is present, otherwise fallback to CPU
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"[CV Engine] Initializing YOLOv8 Neural Network on architecture: {self.device.upper()}")
        self.model = YOLO(model_path)
        self.conf_thresh = conf_thresh
        
        # Extract the model's classification taxonomy
        self.class_map = self.model.names 

    def process_video_stream(self, video_path: str, sample_rate_sec: int = 2) -> list:
        print(f"[CV Engine] Ingesting aerial feed from: {video_path}")
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"CRITICAL ERROR: Unable to establish video stream from {video_path}")
            return []

        # Calculate interval constraints to optimize edge compute performance
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        frame_interval = fps * sample_rate_sec
        
        frame_count = 0
        detections = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process strictly at the designated sample rate (e.g., 1 frame every 2 seconds)
            if frame_count % frame_interval == 0:
                timestamp_sec = round(frame_count / fps, 2)
                print(f"[CV Engine] Extracting and analyzing frame at T+{timestamp_sec}s...")
                
                # Execute zero-shot inference
                results = self.model.predict(source=frame, conf=self.conf_thresh, verbose=False)[0]
                
                frame_anomalies = []
                for box in results.boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    label = self.class_map.get(cls_id, "Unknown Entity")
                    
                    frame_anomalies.append({
                        "label": label,
                        "confidence": round(conf, 2)
                    })

                # Append to the payload only if anomalies are detected in the current frame
                if frame_anomalies:
                    detections.append({
                        "timestamp_sec": timestamp_sec,
                        "anomalies": frame_anomalies
                    })
                    
            frame_count += 1

        cap.release()
        print(f"[CV Engine] Stream analysis complete. Critical anomalies identified in {len(detections)} frames.")
        return detections