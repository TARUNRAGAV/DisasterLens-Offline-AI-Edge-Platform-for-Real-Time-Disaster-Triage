# DisasterLens Technical Design Document (TDD)

## System Architecture
DisasterLens utilizes a decoupled, multi-threaded edge architecture to circumvent hardware blocking and ensure real-time performance on low-power field laptops without cloud reliance.

### Component Diagram
```mermaid
graph TD
    subgraph Edge Hardware
        W[Webcam / Drone Optic]
    end

    subgraph FastAPI Backend
        CT[Capture Thread: 30 FPS Hardware Polling]
        IT[Inference Thread: YOLOv8 Tracking & Heuristics]
        SG[Stream Generator: MJPEG Encoder]
        HE[Health & Telemetry API]
        
        W -->|DirectShow| CT
        CT -->|Latest Frame| IT
        IT -->|Annotated Frame| SG
        IT -->|Metrics| HE
    end

    subgraph React Frontend
        UI[Tactical Dashboard]
        Map[Geospatial TopoMap]
        Rep[SITREP Generator]
        
        SG -->|Multipart/x-mixed-replace| UI
        HE -->|Polling| Map
        HE -->|JSON| Rep
    end