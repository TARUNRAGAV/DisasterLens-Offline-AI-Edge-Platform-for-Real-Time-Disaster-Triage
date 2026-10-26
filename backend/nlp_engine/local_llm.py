import datetime

class OfflineLLMEngine:
    def __init__(self):
        print("[NLP Engine] Booting Edge Synthesis and Formatting Module...")

    def generate_situational_report(self, detection_summary: list) -> str:
        # Failsafe for clean reconnaissance sweeps
        if not detection_summary:
            return "✅ DISASTERLENS: All clear. No anomalies detected in current sector."

        # Construct the emergency SMS header
        report = f"🚨 DISASTERLENS SITREP 🚨\n"
        report += f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Status: ANOMALIES DETECTED\n\n"
        
        # Iterate through the telemetry payload and map to readable alerts
        report += "📍 Aerial Observations:\n"
        for frame in detection_summary:
            time_sec = frame["timestamp_sec"]
            for anomaly in frame["anomalies"]:
                label = anomaly["label"].upper()
                conf = anomaly["confidence"] * 100
                report += f" - T+{time_sec}s: {label} ({conf:.0f}%)\n"
        
        report += "\n⚠️ ACTION: Dispatch SDRF ground units to sector."
        return report