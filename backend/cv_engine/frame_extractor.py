import os
import cv2
from pathlib import Path

class FrameExtractor:
    def __init__(self, output_dir: str = "data/outputs/frames"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_keyframes(self, video_path: str, interval_seconds: int = 2) -> list:
        """Extracts keyframes every N seconds and returns frame metadata."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        frame_interval = fps * interval_seconds
        
        extracted_meta = []
        frame_idx = 0
        saved_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                timestamp_sec = round(frame_idx / fps, 2)
                filename = f"frame_{saved_count:04d}_time_{int(timestamp_sec)}s.jpg"
                save_path = self.output_dir / filename
                
                cv2.imwrite(str(save_path), frame)
                extracted_meta.append({
                    "frame_index": frame_idx,
                    "timestamp_sec": timestamp_sec,
                    "image_path": str(save_path)
                })
                saved_count += 1

            frame_idx += 1

        cap.release()
        print(f"[FrameExtractor] Extracted {saved_count} keyframes to {self.output_dir}")
        return extracted_meta