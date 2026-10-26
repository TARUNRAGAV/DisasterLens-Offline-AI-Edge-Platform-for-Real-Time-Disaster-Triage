import pandas as pd
from pathlib import Path

class TelemetryGeotagger:
    def __init__(self, telemetry_path: str = None):
        self.telemetry_data = None
        if telemetry_path and Path(telemetry_path).exists():
            self.load_telemetry(telemetry_path)

    def load_telemetry(self, file_path: str):
        """Loads CSV containing columns: [timestamp_sec, latitude, longitude, altitude_m]."""
        try:
            self.telemetry_data = pd.read_csv(file_path)
            print(f"[Geotagger] Telemetry loaded: {len(self.telemetry_data)} records.")
        except Exception as e:
            print(f"[Geotagger] Error loading telemetry CSV: {e}")

    def get_coordinates(self, timestamp_sec: float) -> dict:
        """Finds nearest GPS coordinate for a given timestamp in seconds."""
        if self.telemetry_data is None or self.telemetry_data.empty:
            # Fallback default coordinates if telemetry log is missing
            return {"lat": 13.0827, "lon": 80.2707, "alt": 45.0, "estimated": True}

        # Find closest timestamp match
        closest_row = self.telemetry_data.iloc[
            (self.telemetry_data['timestamp_sec'] - timestamp_sec).abs().idxmin()
        ]

        return {
            "lat": float(closest_row['latitude']),
            "lon": float(closest_row['longitude']),
            "alt": float(closest_row['altitude_m']),
            "estimated": False
        }