import cv2
import time
import threading
import logging
import datetime
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import torch
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DisasterLens-Performance")

app = FastAPI(title="DisasterLens API - Optimized Edge")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
try:
    logger.info(f"Loading YOLOv8n onto {device.upper()}...")
    model = YOLO("models/yolov8n.pt")
except Exception as e:
    logger.error(f"Model load failed: {e}")
    model = None

sdrf_telemetry = {
    "hazards": [],
    "metrics": {
        "unique_civilians": 0, "mre_req": 0, 
        "compute_status": "STANDBY", 
        "water_depth_class": "UNKNOWN", "water_severity": "gray"
    }
}
tracked_civilians = set()
diagnostics = {
    "capture_fps": 0.0, "inference_ms": 0.0, "display_fps": 0.0,
    "device": device.upper(), "camera_state": "OFFLINE", "dropped_frames": 0
}

class VideoPipeline:
    def __init__(self):
        self.cap = None
        self.running = False
        self.latest_frame = None
        self.annotated_frame = None
        self.lock = threading.Lock()
        
    def start(self, source=0):
        if self.running: return True
        logger.info("Initializing hardware capture pipeline...")
        self.cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        if not self.cap.isOpened() or not self.cap.read()[0]:
            self.cap.release()
            self.cap = cv2.VideoCapture(source)
            
        if not self.cap.isOpened():
            diagnostics["camera_state"] = "ERROR"
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.running = True
        diagnostics["camera_state"] = "LIVE"
        
        threading.Thread(target=self._capture_loop, daemon=True).start()
        threading.Thread(target=self._inference_loop, daemon=True).start()
        return True

    def stop(self):
        self.running = False
        if self.cap: self.cap.release()
        diagnostics["camera_state"] = "STOPPED"
        logger.info("Pipeline terminated safely.")

    def _capture_loop(self):
        prev_time = time.time()
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                with self.lock: self.latest_frame = frame
                curr_time = time.time()
                diagnostics["capture_fps"] = round(1.0 / (curr_time - prev_time + 0.0001), 1)
                prev_time = curr_time
            else:
                time.sleep(0.01)

    def _inference_loop(self):
        global sdrf_telemetry, tracked_civilians
        base_lat, base_lon = 13.0827, 80.2707
        while self.running:
            frame = None
            with self.lock:
                if self.latest_frame is not None: frame = self.latest_frame.copy()
            
            if frame is None or model is None:
                time.sleep(0.05)
                continue

            start_infer = time.time()
            results = model.track(frame, persist=True, conf=0.35, imgsz=320, verbose=False)
            boxes = results[0].boxes
            hazard_detected = False
            depth_class, depth_color = "UNKNOWN", "gray"

            if boxes.id is not None:
                track_ids = boxes.id.int().tolist()
                for box, track_id in zip(boxes, track_ids):
                    cls_id = int(box.cls[0].item())
                    label = model.names.get(cls_id, "unknown").lower()
                    if label == "person":
                        hazard_detected = True
                        tracked_civilians.add(track_id)
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        aspect_ratio = (x2 - x1) / (y2 - y1) if (y2 - y1) > 0 else 1
                        if aspect_ratio > 0.8: depth_class, depth_color = "SWIMMING-DEPTH / SUBMERGED", "red"
                        elif aspect_ratio > 0.45: depth_class, depth_color = "HIP-LEVEL / DEEP WATER", "orange"
                        else: depth_class, depth_color = "WALKABLE", "green"
            
            if hazard_detected:
                sdrf_telemetry["metrics"].update({"compute_status": "ACTIVE TRACKING", "water_depth_class": depth_class, "water_severity": depth_color})
                if len(sdrf_telemetry["hazards"]) == 0 or (time.time() - getattr(self, 'last_log_time', 0)) > 2:
                    sdrf_telemetry["hazards"].append({
                        "lat": base_lat + (len(sdrf_telemetry["hazards"]) * 0.0001), 
                        "lon": base_lon + (len(sdrf_telemetry["hazards"]) * 0.0001), 
                        "depth": depth_class, "color": depth_color, 
                        "timestamp": datetime.datetime.now().strftime('%H:%M:%S')
                    })
                    if len(sdrf_telemetry["hazards"]) > 50: sdrf_telemetry["hazards"].pop(0)
                    self.last_log_time = time.time()
            else:
                sdrf_telemetry["metrics"].update({"compute_status": "IDLE / SCANNING", "water_depth_class": "UNKNOWN", "water_severity": "gray"})

            sdrf_telemetry["metrics"]["unique_civilians"] = len(tracked_civilians)
            sdrf_telemetry["metrics"]["mre_req"] = len(tracked_civilians) * 2

            with self.lock: self.annotated_frame = results[0].plot()
            diagnostics["inference_ms"] = round((time.time() - start_infer) * 1000, 1)

pipeline = VideoPipeline()

def stream_generator():
    import numpy as np
    prev_time = time.time()
    while pipeline.running:
        frame = None
        with pipeline.lock:
            if pipeline.annotated_frame is not None: frame = pipeline.annotated_frame.copy()
            elif pipeline.latest_frame is not None: frame = pipeline.latest_frame.copy()
                
        if frame is not None:
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            curr_time = time.time()
            diagnostics["display_fps"] = round(1.0 / (curr_time - prev_time + 0.0001), 1)
            prev_time = curr_time
        time.sleep(1/30)

@app.get("/api/stream_live")
def stream_live_drone():
    import numpy as np
    if not pipeline.start():
        err_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(err_frame, "WEBCAM UNAVAILABLE", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        ret, buffer = cv2.imencode('.jpg', err_frame)
        return StreamingResponse(iter([b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n']), media_type="multipart/x-mixed-replace; boundary=frame")
    return StreamingResponse(stream_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/stream_stop")
def stream_stop():
    pipeline.stop()
    return {"status": "stopped"}

@app.get("/api/telemetry")
def get_telemetry():
    return sdrf_telemetry

@app.get("/api/diagnostics")
def get_diagnostics():
    return diagnostics

@app.get("/api/health")
def system_health():
    return JSONResponse({"api": "operational", "camera": diagnostics["camera_state"]})

@app.post("/api/sitrep/generate")
def generate_sitrep():
    civ = sdrf_telemetry["metrics"]["unique_civilians"]
    depth = sdrf_telemetry["metrics"]["water_depth_class"]
    haz = len(sdrf_telemetry["hazards"])
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if civ == 0 and haz == 0:
        return {"report": f"✅ SITREP [{ts}]\nSECTOR SECURE. No confirmed civilians or hazards logged. Awaiting telemetry."}
    
    report = f"🚨 OFFICIAL SITREP [{ts}]\nSTATUS: ACTIVE INCIDENT\n\nVERIFIED DATA:\n- Unique Civilians Stranded: {civ}\n- Rations Required: {civ * 2}\n- Primary Flood Assessment: {depth}\n- Logged Hazard Events: {haz}\n\nWARNING:\nGeometric depth classification is an estimate. Ensure physical {depth} clearance before dispatching ground units."
    return {"report": report}