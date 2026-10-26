# DisasterLens: Offline AI Edge Platform for Real-Time Disaster Triage

DisasterLens is an offline-first edge-computing platform designed for State Disaster Response Forces (SDRF). It leverages computer vision (YOLOv8) and asynchronous multi-threading to process live camera feeds, mapping stranded civilians, estimating floodwater depth geometrically, and generating deterministic Situation Reports (SITREPs) without requiring cloud connectivity.

## Core Features
*   **Decoupled Edge Pipeline:** Multi-threaded architecture separates webcam hardware capture, AI inference, and network streaming to guarantee zero-lag video feeds on standard field laptops.
*   **Geometric Water-Depth Heuristics:** Evaluates bounding-box aspect ratios to classify flood hazards (Walkable, Hip-Level, Submerged).
*   **Tactical Geospatial Mapping:** Integrates OpenTopoMap telemetry to plot identified hazards and civilians.
*   **Deterministic SITREP Engine:** Compiles verified telemetry into exportable incident reports.

## Tech Stack
*   **Backend:** Python 3.14+, FastAPI, OpenCV (DirectShow), Ultralytics (YOLOv8 Nano), Uvicorn.
*   **Frontend:** React, Vite, Axios, React-Leaflet, Lucide-React.

## Quick Start
See `docs/SETUP.md` for comprehensive Windows installation instructions.

## License
MIT License. See `LICENSE` for details.