import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, Map as MapIcon, ShieldAlert, Users, Package, Waves, Cpu, Wifi, Power, AlertTriangle, FileText, Settings, Download, ActivitySquare } from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [activeView, setActiveView] = useState("monitoring");
  const [feedMode, setFeedMode] = useState("idle");
  const [streamUrl, setStreamUrl] = useState(null);
  
  const [health, setHealth] = useState({ api: "offline", camera: "OFFLINE" });
  const [diagnostics, setDiagnostics] = useState({ capture_fps: 0, inference_ms: 0, display_fps: 0, device: "UNKNOWN" });
  const [sitrep, setSitrep] = useState("");
  
  const [telemetry, setTelemetry] = useState({ 
    hazards: [], metrics: { unique_civilians: 0, mre_req: 0, compute_status: "STANDBY", water_depth_class: "UNKNOWN", water_severity: "gray" }
  });

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/health`);
        setHealth(res.data);
      } catch (err) {
        setHealth({ api: "offline", camera: "ERROR" });
      }
    };
    fetchHealth();
    const healthTimer = setInterval(fetchHealth, 3000);

    let dataTimer;
    if (feedMode === "live") {
      dataTimer = setInterval(async () => {
        try {
          const [telRes, diagRes] = await Promise.all([ axios.get(`${API_BASE}/api/telemetry`), axios.get(`${API_BASE}/api/diagnostics`) ]);
          setTelemetry(telRes.data);
          setDiagnostics(diagRes.data);
        } catch (err) {}
      }, 1000);
    }
    return () => { clearInterval(healthTimer); clearInterval(dataTimer); };
  }, [feedMode]);

  const toggleFeed = async () => {
    if (feedMode === "live") {
      setFeedMode("idle");
      setStreamUrl(null);
      await axios.get(`${API_BASE}/api/stream_stop`);
    } else {
      setFeedMode("live");
      setStreamUrl(`${API_BASE}/api/stream_live?t=${Date.now()}`);
    }
  };

  const generateSITREP = async () => {
    setSitrep("Compiling verified telemetry...");
    try {
      const res = await axios.post(`${API_BASE}/api/sitrep/generate`);
      setSitrep(res.data.report);
    } catch (err) {
      setSitrep(`❌ API ERROR: Backend unreachable.`);
    }
  };

  const exportSITREP = () => {
    const report = `DISASTERLENS OFFICIAL EXPORT\nDate: ${new Date().toLocaleString()}\n\nSummary:\n${sitrep || "No SITREP generated."}\n\nMetrics:\n- Civilians Logged: ${telemetry.metrics.unique_civilians}\n- Water Depth: ${telemetry.metrics.water_depth_class}\n- Hazards Logged: ${telemetry.hazards.length}`;
    const blob = new Blob([report], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `DisasterLens_SITREP_${Date.now()}.txt`;
    a.click();
  };

  const severityColors = { green: '#10b981', orange: '#f59e0b', red: '#ef4444', gray: '#6b7280' };
  const waterColor = severityColors[telemetry.metrics.water_severity];

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#090a0f', color: '#e5e7eb', fontFamily: 'sans-serif' }}>
      <nav style={{ width: '260px', backgroundColor: '#13161f', borderRight: '1px solid #1f2937', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '24px 20px', borderBottom: '1px solid #1f2937' }}>
          <h2 style={{margin:0, color:'#06b6d4', display:'flex', alignItems:'center', gap:'8px'}}><AlertTriangle/> DisasterLens</h2>
        </div>
        <div style={{ flex: 1, padding: '20px 10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <NavItem icon={<Activity size={18}/>} label="Live Monitoring" active={activeView === "monitoring"} onClick={() => setActiveView("monitoring")} />
          <NavItem icon={<MapIcon size={18}/>} label="Geospatial Map" active={activeView === "map"} onClick={() => setActiveView("map")} />
          <NavItem icon={<ShieldAlert size={18}/>} label="Detection Logs" active={activeView === "logs"} onClick={() => setActiveView("logs")} />
          <NavItem icon={<FileText size={18}/>} label="SITREP Exports" active={activeView === "export"} onClick={() => setActiveView("export")} />
        </div>
        <div style={{ padding: '20px', borderTop: '1px solid #1f2937' }}>
          <NavItem icon={<Settings size={18}/>} label="System Settings" active={activeView === "settings"} onClick={() => setActiveView("settings")} />
        </div>
      </nav>

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <header style={{ height: '70px', backgroundColor: '#090a0f', borderBottom: '1px solid #1f2937', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px' }}>
          <h1 style={{ fontSize: '18px', fontWeight: '600', margin: 0, textTransform: 'uppercase' }}>{activeView.replace("-", " ")}</h1>
          <div style={{ display: 'flex', gap: '20px' }}>
            <HealthIndicator label="API" status={health.api} />
            <HealthIndicator label="Webcam" status={health.camera === "LIVE" ? "operational" : (health.camera === "ERROR" ? "error" : "standby")} />
          </div>
        </header>

        {activeView === "monitoring" && (
          <div style={{ flex: 1, padding: '24px', display: 'grid', gridTemplateColumns: '3fr 2fr', gridTemplateRows: 'auto 1fr', gap: '24px', overflowY: 'auto' }}>
            <div style={{ gridColumn: '1 / -1', display: 'flex', gap: '16px' }}>
              <MetricCard icon={<Users color="#3b82f6"/>} label="Unique Civilians" value={telemetry.metrics.unique_civilians} />
              <div style={{ flex: 1.5, backgroundColor: '#13161f', border: `1px solid ${waterColor}`, borderRadius: '8px', padding: '16px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ backgroundColor: '#1f2937', padding: '10px', borderRadius: '8px' }}><Waves color={waterColor} /></div>
                <div>
                  <div style={{ color: '#9ca3af', fontSize: '12px', fontWeight: '500', marginBottom: '4px' }}>Water Depth Classification</div>
                  <div style={{ fontSize: '18px', fontWeight: '700', color: waterColor }}>{telemetry.metrics.water_depth_class}</div>
                </div>
              </div>
              <div style={{ flex: 1, backgroundColor: '#13161f', border: `1px solid #1f2937`, borderRadius: '8px', padding: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <span style={{ color: '#9ca3af', fontSize: '12px', fontWeight: '500', marginBottom: '4px' }}>AI ENGINE</span>
                <span style={{ color: telemetry.metrics.compute_status.includes("ACTIVE") ? '#ef4444' : '#10b981', fontWeight: 'bold', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Cpu size={14} /> {telemetry.metrics.compute_status}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ backgroundColor: '#13161f', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '12px 16px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '14px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}><Wifi size={16} color={feedMode === "live" ? "#10b981" : "#6b7280"} /> Local Webcam Uplink</span>
                  <button onClick={toggleFeed} style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: feedMode === "live" ? '#ef4444' : '#3b82f6', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: '4px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}>
                    <Power size={14} /> {feedMode === "live" ? "STOP CAMERA" : "START CAMERA"}
                  </button>
                </div>
                <div style={{ height: '360px', backgroundColor: '#000', position: 'relative' }}>
                  {feedMode === "live" && streamUrl ? <img src={streamUrl} alt="Live Stream" style={{ width: '100%', height: '100%', objectFit: 'contain' }} onError={(e) => { e.target.style.display='none'; document.getElementById('vid-err').style.display='flex'; }} /> : null}
                  <div id="vid-err" style={{ display: feedMode === "live" && streamUrl ? 'none' : 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: '#4b5563', flexDirection: 'column', gap: '12px' }}><AlertTriangle size={32} /><span>{feedMode === "live" ? "CAMERA IN USE BY ANOTHER APP" : "WEBCAM STOPPED"}</span></div>
                </div>
              </div>

              <div style={{ backgroundColor: '#13161f', border: '1px solid #1f2937', borderRadius: '8px', padding: '12px 16px', display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                 <span style={{color: '#9ca3af', display: 'flex', alignItems: 'center', gap:'6px'}}><ActivitySquare size={14}/> <strong>PROFILER:</strong></span>
                 <span>Capture: <strong style={{color: '#fff'}}>{diagnostics.capture_fps} FPS</strong></span>
                 <span>Inference: <strong style={{color: '#fff'}}>{diagnostics.inference_ms} ms</strong></span>
                 <span>Stream: <strong style={{color: '#fff'}}>{diagnostics.display_fps} FPS</strong></span>
                 <span>Core: <strong style={{color: '#10b981'}}>{diagnostics.device}</strong></span>
              </div>

              <div style={{ flex: 1, backgroundColor: '#13161f', border: '1px solid #1f2937', borderRadius: '8px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '12px 16px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '14px', fontWeight: '600' }}>Live SITREP (Deterministic)</span>
                  <button onClick={generateSITREP} style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#10b981', color: '#fff', border: 'none', padding: '6px 14px', borderRadius: '4px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}><FileText size={14} /> COMPILE DATA</button>
                </div>
                <textarea value={sitrep} readOnly placeholder="Awaiting verified incident data..." style={{ flex: 1, backgroundColor: '#0f111a', color: '#06b6d4', border: 'none', padding: '16px', outline: 'none', resize: 'none', fontFamily: 'monospace', fontSize: '13px', lineHeight: '1.6' }} />
              </div>
            </div>

            <div style={{ backgroundColor: '#13161f', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
               <div style={{ padding: '12px 16px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between' }}><span style={{ fontSize: '14px', fontWeight: '600' }}>Geospatial Intelligence</span></div>
                <div style={{ flex: 1, backgroundColor: '#0f111a' }}>
                  <MapContainer center={[13.0827, 80.2707]} zoom={15} style={{ height: '100%', width: '100%', zIndex: 0 }}>
                    <TileLayer url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png" />
                    {telemetry.hazards.map((hazard, i) => (
                      <CircleMarker key={i} center={[hazard.lat, hazard.lon]} radius={10} color={severityColors[hazard.color]} fillOpacity={0.6}>
                        <Popup><strong>{hazard.depth}</strong><br/>Time: {hazard.timestamp}</Popup>
                      </CircleMarker>
                    ))}
                  </MapContainer>
                </div>
            </div>
          </div>
        )}

        {activeView === "map" && (
          <div style={{ flex: 1, padding: '24px' }}>
            <div style={{ height: '100%', borderRadius: '8px', overflow: 'hidden', border: '1px solid #1f2937' }}>
              <MapContainer center={[13.0827, 80.2707]} zoom={15} style={{ height: '100%', width: '100%', zIndex: 0 }}>
                <TileLayer url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png" />
                {telemetry.hazards.map((hazard, i) => (
                  <CircleMarker key={i} center={[hazard.lat, hazard.lon]} radius={10} color={severityColors[hazard.color]} fillOpacity={0.6}><Popup><strong>{hazard.depth}</strong><br/>Time: {hazard.timestamp}</Popup></CircleMarker>
                ))}
              </MapContainer>
            </div>
          </div>
        )}

        {activeView === "logs" && (
          <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #374151', color: '#9ca3af' }}>
                  <th style={{ padding: '12px' }}>Timestamp</th>
                  <th style={{ padding: '12px' }}>Classification</th>
                  <th style={{ padding: '12px' }}>Coordinates</th>
                </tr>
              </thead>
              <tbody>
                {telemetry.hazards.length === 0 ? <tr><td colSpan="3" style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>No incidents logged during this session.</td></tr> : null}
                {telemetry.hazards.slice().reverse().map((h, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #1f2937' }}><td style={{ padding: '12px' }}>{h.timestamp}</td><td style={{ padding: '12px', color: severityColors[h.color] }}>{h.depth}</td><td style={{ padding: '12px', fontFamily: 'monospace' }}>{h.lat.toFixed(5)}, {h.lon.toFixed(5)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeView === "export" && (
          <div style={{ padding: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
            <FileText size={64} color="#3b82f6" />
            <h2>SITREP Document Export</h2>
            <button onClick={exportSITREP} style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#10b981', color: '#fff', border: 'none', padding: '12px 24px', borderRadius: '4px', fontSize: '16px', cursor: 'pointer' }}><Download size={18} /> Download Official SITREP</button>
          </div>
        )}

        {activeView === "settings" && (
          <div style={{ padding: '40px', color: '#9ca3af', maxWidth: '600px' }}>
            <h2 style={{ color: '#fff' }}>System Configuration</h2>
            <div style={{ marginTop: '20px', padding: '20px', backgroundColor: '#13161f', borderRadius: '8px', border: '1px solid #1f2937' }}>
              <label style={{ display: 'block', marginBottom: '8px', color: '#fff' }}>YOLO Target Inference Resolution</label>
              <select disabled style={{ width: '100%', padding: '10px', backgroundColor: '#1f2937', color: '#fff', border: 'none', borderRadius: '4px' }}><option>320x320 (Optimized Edge Performance)</option></select>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

const NavItem = ({ icon, label, active, onClick }) => (
  <div onClick={onClick} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 16px', borderRadius: '6px', backgroundColor: active ? '#1f2937' : 'transparent', color: active ? '#fff' : '#9ca3af', cursor: 'pointer', transition: 'all 0.2s' }}>{icon} <span style={{ fontSize: '14px', fontWeight: '500' }}>{label}</span></div>
);
const HealthIndicator = ({ label, status }) => {
  const colors = { operational: '#10b981', standby: '#f59e0b', offline: '#6b7280', error: '#ef4444' };
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}><div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: colors[status] || '#6b7280' }} /><span style={{ color: '#9ca3af' }}>{label}: <span style={{ color: '#e5e7eb', textTransform: 'uppercase' }}>{status}</span></span></div>
  );
};
const MetricCard = ({ icon, label, value }) => (
  <div style={{ flex: 1, backgroundColor: '#13161f', border: '1px solid #1f2937', borderRadius: '8px', padding: '16px', display: 'flex', alignItems: 'center', gap: '16px' }}><div style={{ backgroundColor: '#1f2937', padding: '10px', borderRadius: '8px' }}>{icon}</div><div><div style={{ color: '#9ca3af', fontSize: '12px', fontWeight: '500', marginBottom: '4px' }}>{label}</div><div style={{ fontSize: '20px', fontWeight: '700', color: '#f3f4f6' }}>{value}</div></div></div>
);