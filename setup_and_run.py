import os
import urllib.request
from backend.cv_engine.detector import DisasterDetector
from backend.nlp_engine.local_llm import OfflineLLMEngine

def fetch_assets():
    print("--- INITIATING ASSET ACQUISITION ---")
    
    # 1. Fetch the Ultralytics YOLOv8 Nano Weights
    model_path = "models/yolov8n.pt"
    if not os.path.exists(model_path):
        print("Downloading YOLOv8 Nano model weights...")
        urllib.request.urlretrieve("https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8n.pt", model_path)
        print("✅ Model weights secured.")
    else:
        print("✅ Model weights already exist locally.")

    # 2. Fetch the Sample Video Feed (Fixed 403 Error)
    video_path = "data/raw_videos/sample.mp4"
    if not os.path.exists(video_path):
        print("Downloading sample aerial video feed...")
        
        # Switched to an Intel CV sample video and added a browser User-Agent to bypass server blocks
        url = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        
        with urllib.request.urlopen(req) as response, open(video_path, 'wb') as out_file:
            out_file.write(response.read())
            
        print("✅ Sample video secured.")
    else:
        print("✅ Sample video already exists locally.")

def execute_pipeline():
    print("\n--- INITIATING DISASTERLENS PIPELINE ---")
    
    # Initialize the computer vision engine
    detector = DisasterDetector(model_path="models/yolov8n.pt")
    
    # Execute the video stream analysis
    results = detector.process_video_stream(video_path="data/raw_videos/sample.mp4", sample_rate_sec=2)
    
    # Synthesize the Situational Report
    llm = OfflineLLMEngine()
    sitrep_text = llm.generate_situational_report(results)
    
    print("\n========================================")
    print("FINAL SMS ALERT OUTPUT GENERATED:")
    print("========================================")
    print(sitrep_text)
    print("========================================")

if __name__ == "__main__":
    fetch_assets()
    execute_pipeline()