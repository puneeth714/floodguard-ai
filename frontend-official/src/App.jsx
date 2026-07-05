import React, { useState, useEffect, useRef } from 'react';
import { APIProvider, Map, AdvancedMarker, InfoWindow, useMap, useMapsLibrary } from '@vis.gl/react-google-maps';
import './App.css';

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : window.location.protocol + '//' + window.location.hostname + ':8000';

// Inner component to render weighted Google Maps Heatmap Layer
function HeatmapOverlay({ points, visible }) {
  const map = useMap();
  const visualization = useMapsLibrary('visualization');
  const [heatmapInstance, setHeatmapInstance] = useState(null);

  useEffect(() => {
    if (!map || !visualization) return;

    if (heatmapInstance) {
      heatmapInstance.setMap(null);
    }

    if (!visible || !points || points.length === 0) {
      return;
    }

    const google = window.google;
    const heatmapPoints = points.map(p => ({
      location: new google.maps.LatLng(p.lat, p.lng),
      weight: p.fvi
    }));

    const heatmap = new visualization.HeatmapLayer({
      data: heatmapPoints,
      map: map,
      radius: 40,
      opacity: 0.65
    });

    setHeatmapInstance(heatmap);

    return () => {
      heatmap.setMap(null);
    };
  }, [map, visualization, points, visible]);

  return null;
}

// Inner component to render weather radar storm cells
function RadarCircleOverlay({ cloud, visible }) {
  const map = useMap();
  const [circleInstance, setCircleInstance] = useState(null);

  useEffect(() => {
    if (!map) return;

    if (circleInstance) {
      circleInstance.setMap(null);
    }

    if (!visible || !cloud) return;

    const strokeColor = cloud.intensity === 'heavy' ? '#ff3366' : '#00e5ff';
    const fillColor = cloud.intensity === 'heavy' ? 'rgba(255, 51, 102, 0.12)' : 'rgba(0, 229, 255, 0.08)';

    const circle = new window.google.maps.Circle({
      strokeColor: strokeColor,
      strokeOpacity: 0.7,
      strokeWeight: 2,
      fillColor: fillColor,
      fillOpacity: 0.35,
      map: map,
      center: { lat: cloud.lat, lng: cloud.lng },
      radius: cloud.radius_m
    });

    setCircleInstance(circle);

    return () => {
      circle.setMap(null);
    };
  }, [map, cloud, visible]);

  return null;
}

function App() {
  const [activeSos, setActiveSos] = useState([]);
  const [drains, setDrains] = useState([]);
  const [pumps, setPumps] = useState([]);
  const [fviHeatmap, setFviHeatmap] = useState([]);
  const [weatherRadar, setWeatherRadar] = useState([]);

  // Layers Toggles
  const [layers, setLayers] = useState({
    heatmap: true,
    drains: true,
    pumps: true,
    radar: true,
    sos: true
  });

  const [activeTab, setActiveTab] = useState('alerts'); // 'alerts' | 'chat'
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'welcome',
      role: 'ai',
      content: 'System Initialized. Access to guideline search (RAG) and simulation engines authenticated. Enter What-If queries below.'
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Active Map Selection
  const [selectedPin, setSelectedPin] = useState(null);
  const mapRef = useRef(null);

  // Fetch initial dashboard records
  const fetchDashboardData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/official/dashboard-summary`);
      if (!res.ok) throw new Error("Dashboard fetch failed");
      const data = await res.json();
      
      setActiveSos(data.active_sos || []);
      setDrains(data.drains || []);
      setPumps(data.pumps || []);
      setFviHeatmap(data.fvi_heatmap || []);
      setWeatherRadar(data.weather_radar || []);
    } catch (err) {
      console.error("Error fetching dashboard details:", err);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // Connect to SSE stream for live updates
    const eventSource = new EventSource(`${API_BASE}/api/official/live-sos-feed`);

    eventSource.addEventListener('new_sos', (e) => {
      const newAlert = JSON.parse(e.data);
      console.log("New distress signal streamed via SSE:", newAlert);
      setActiveSos(prev => {
        // Avoid duplicate session_ids
        if (prev.some(a => a.session_id === newAlert.session_id)) return prev;
        return [newAlert, ...prev];
      });
    });

    eventSource.addEventListener('update_sos', (e) => {
      const updatedAlert = JSON.parse(e.data);
      console.log("Vision analysis update streamed via SSE:", updatedAlert);
      setActiveSos(prev =>
        prev.map(a => a.session_id === updatedAlert.session_id ? { ...a, ...updatedAlert } : a)
      );
    });

    return () => {
      eventSource.close();
    };
  }, []);

  const handleSendChat = async () => {
    if (!chatInput.trim()) return;

    const userText = chatInput;
    setChatMessages(prev => [...prev, { id: `u_${Date.now()}`, role: 'official', content: userText }]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/official/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 'official_console_session',
          user_query: userText
        })
      });

      if (!response.ok) throw new Error("Console communication failed");
      const data = await response.json();

      setChatMessages(prev => [
        ...prev,
        { id: `ai_${Date.now()}`, role: 'ai', content: data.final_response }
      ]);
    } catch (err) {
      console.error(err);
      setChatMessages(prev => [
        ...prev,
        { id: `err_${Date.now()}`, role: 'ai', content: 'Communication loss encountered with simulation agent.' }
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Trigger simulated pump toggle
  const togglePumpStatus = (pumpId) => {
    setPumps(prev =>
      prev.map(p => {
        if (p.pump_id === pumpId) {
          const nextStatus = p.status === 'active' ? 'stopped' : 'active';
          // Simulate FVI changes if toggled
          if (nextStatus === 'active') {
            setFviHeatmap(h => h.map(point => ({ ...point, fvi: Math.max(10.0, point.fvi - 12.0) })));
          } else {
            setFviHeatmap(h => h.map(point => ({ ...point, fvi: Math.min(100.0, point.fvi + 12.0) })));
          }
          return { ...p, status: nextStatus };
        }
        return p;
      })
    );
  };

  // Trigger simulated drain cleaning
  const toggleDrainStatus = (drainId) => {
    setDrains(prev =>
      prev.map(d => {
        if (d.drain_id === drainId) {
          const nextStatus = d.status === 'blocked' ? 'cleared' : 'blocked';
          // Simulate FVI decrease if desilted
          if (nextStatus === 'cleared') {
            setFviHeatmap(h => h.map(point => ({ ...point, fvi: Math.max(15.0, point.fvi - 8.0) })));
          } else {
            setFviHeatmap(h => h.map(point => ({ ...point, fvi: Math.min(100.0, point.fvi + 8.0) })));
          }
          return { ...d, status: nextStatus };
        }
        return d;
      })
    );
  };

  const handleDownloadReport = (content) => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `floodguard_municipal_report_${Date.now()}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const centerOnMarker = (lat, lng) => {
    if (mapRef.current) {
      mapRef.current.panTo({ lat, lng });
      mapRef.current.setZoom(16);
    }
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="dashboard-header">
        <div className="header-brand">
          <span className="brand-badge">Official Console</span>
          <span className="brand-title">FloodGuard Decision Intelligence Portal</span>
        </div>
        <div className="header-metrics">
          <div className="metric-item">
            <span className="metric-value red">{activeSos.filter(s => s.status !== 'rescued').length}</span>
            <span className="metric-label">Active SOS Signals</span>
          </div>
          <div className="metric-item">
            <span className="metric-value orange">{drains.filter(d => d.status === 'blocked').length}</span>
            <span className="metric-label">Blocked Drains</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Split */}
      <div className="dashboard-workspace">
        {/* Left Map */}
        <div className="map-wrapper">
          <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
            <Map
              defaultCenter={{ lat: 12.9279, lng: 77.6271 }}
              defaultZoom={14}
              mapId="DEMO_MAP_ID"
              gestureHandling="greedy"
              disableDefaultUI={true}
              onLoad={(map) => { mapRef.current = map; }}
            >
              {/* Heatmap Overlay */}
              <HeatmapOverlay points={fviHeatmap} visible={layers.heatmap} />

              {/* Storm Cells overlays */}
              {weatherRadar.map(cloud => (
                <RadarCircleOverlay key={cloud.cloud_id} cloud={cloud} visible={layers.radar} />
              ))}

              {/* Storm Drains markers */}
              {layers.drains && drains.map(drain => (
                <AdvancedMarker
                  key={drain.drain_id}
                  position={{ lat: drain.lat, lng: drain.lng }}
                  onClick={() => setSelectedPin({ type: 'drain', ...drain })}
                >
                  <div className={`custom-drain-pin ${drain.status}`} />
                </AdvancedMarker>
              ))}

              {/* Suction Pumps markers */}
              {layers.pumps && pumps.map(pump => (
                <AdvancedMarker
                  key={pump.pump_id}
                  position={{ lat: pump.lat, lng: pump.lng }}
                  onClick={() => setSelectedPin({ type: 'pump', ...pump })}
                >
                  <div className={`custom-pump-pin ${pump.status}`} />
                </AdvancedMarker>
              ))}

              {/* Real-time distress SOS markers */}
              {layers.sos && activeSos.map(sos => (
                <AdvancedMarker
                  key={sos.session_id}
                  position={{ lat: sos.lat, lng: sos.lng }}
                  onClick={() => setSelectedPin({ type: 'sos', ...sos })}
                >
                  <div className={`custom-sos-pin ${sos.status}`} />
                </AdvancedMarker>
              ))}

              {/* Popup details modal inside Map */}
              {selectedPin && (
                <InfoWindow
                  position={{ lat: selectedPin.lat, lng: selectedPin.lng }}
                  onCloseClick={() => setSelectedPin(null)}
                >
                  <div className="map-popup-window">
                    {selectedPin.type === 'sos' && (
                      <>
                        <div className="popup-title">Stranded Resident Alert</div>
                        {selectedPin.photo_url && (
                          <img src={`${API_BASE}${selectedPin.photo_url}`} className="popup-img" alt="SOS flood condition" />
                        )}
                        <p><strong>Status:</strong> {selectedPin.status.toUpperCase()}</p>
                        <p><strong>Predicted Depth:</strong> {selectedPin.detected_depth ? `${selectedPin.detected_depth} cm` : 'Evaluating...'}</p>
                        <p className="popup-meta">Coords: {selectedPin.lat.toFixed(5)}, {selectedPin.lng.toFixed(5)}</p>
                      </>
                    )}
                    {selectedPin.type === 'pump' && (
                      <>
                        <div className="popup-title">Mechanical Suction Pump</div>
                        <p><strong>Unit Name:</strong> {selectedPin.name}</p>
                        <p><strong>Flow Capacity:</strong> {selectedPin.flow_rate_lps} L/sec</p>
                        <p><strong>Status:</strong> {selectedPin.status.toUpperCase()}</p>
                        <button
                          className="popup-btn"
                          onClick={() => togglePumpStatus(selectedPin.pump_id)}
                        >
                          {selectedPin.status === 'active' ? 'Stop Pump' : 'Start Pump'}
                        </button>
                      </>
                    )}
                    {selectedPin.type === 'drain' && (
                      <>
                        <div className="popup-title">Stormwater Drain Pipe</div>
                        <p><strong>Drain Name:</strong> {selectedPin.name}</p>
                        <p><strong>Status:</strong> {selectedPin.status === 'blocked' ? '🚫 BLOCKED (Heavy Silting)' : '✓ CLEARED'}</p>
                        <button
                          className="popup-btn"
                          onClick={() => toggleDrainStatus(selectedPin.drain_id)}
                        >
                          {selectedPin.status === 'blocked' ? 'Clear Drain' : 'Block Drain'}
                        </button>
                      </>
                    )}
                  </div>
                </InfoWindow>
              )}
            </Map>
          </APIProvider>

          {/* Floating layers selector panel */}
          <div className="map-controls-panel glass-panel">
            <p className="panel-title">Operational Layers</p>
            <label className="control-option">
              <input
                type="checkbox"
                className="control-checkbox"
                checked={layers.heatmap}
                onChange={() => setLayers(p => ({ ...p, heatmap: !p.heatmap }))}
              />
              FVI Heatmap
            </label>
            <label className="control-option">
              <input
                type="checkbox"
                className="control-checkbox"
                checked={layers.radar}
                onChange={() => setLayers(p => ({ ...p, radar: !p.radar }))}
              />
              Storm Cover Radar
            </label>
            <label className="control-option">
              <input
                type="checkbox"
                className="control-checkbox"
                checked={layers.sos}
                onChange={() => setLayers(p => ({ ...p, sos: !p.sos }))}
              />
              Resident SOS Pins
            </label>
            <label className="control-option">
              <input
                type="checkbox"
                className="control-checkbox"
                checked={layers.drains}
                onChange={() => setLayers(p => ({ ...p, drains: !p.drains }))}
              />
              Municipal Drains
            </label>
            <label className="control-option">
              <input
                type="checkbox"
                className="control-checkbox"
                checked={layers.pumps}
                onChange={() => setLayers(p => ({ ...p, pumps: !p.pumps }))}
              />
              Tactical Water Pumps
            </label>
          </div>

          {/* Legend Overlay */}
          <div className="map-legend glass-panel">
            <div className="legend-row">
              <div className="legend-color heatmap" />
              <span>Vulnerability Index (FVI)</span>
            </div>
            <div className="legend-row">
              <div className="legend-color pump-active" />
              <span>Tactical Water Pump</span>
            </div>
            <div className="legend-row">
              <div className="legend-color drain-blocked" />
              <span>Stormwater Drain</span>
            </div>
            <div className="legend-row">
              <div className="legend-color cloud-cover" />
              <span>Dashed Radar Rain Cells</span>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="sidebar-wrapper">
          <div className="sidebar-tabs">
            <button
              className={`tab-btn ${activeTab === 'alerts' ? 'active' : ''}`}
              onClick={() => setActiveTab('alerts')}
            >
              Distress Feed ({activeSos.length})
            </button>
            <button
              className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              Simulations Console
            </button>
          </div>

          <div className="tab-content-panel">
            {/* Tab 1: Live Alerts Feed */}
            {activeTab === 'alerts' && (
              <div className="alerts-feed-container">
                {activeSos.length === 0 ? (
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13px', textAlign: 'center', marginTop: '40px' }}>
                    No active distress signals reported.
                  </p>
                ) : (
                  activeSos.map(sos => (
                    <div
                      key={sos.session_id}
                      className={`alert-card ${sos.status}`}
                      onClick={() => {
                        setSelectedPin({ type: 'sos', ...sos });
                        centerOnMarker(sos.lat, sos.lng);
                      }}
                    >
                      <div className="alert-card-header">
                        <span className="alert-title">Distress Session: {sos.session_id}</span>
                        <span className={`alert-badge ${sos.status}`}>{sos.status}</span>
                      </div>
                      <div className="alert-body">
                        {sos.photo_url && (
                          <img src={`${API_BASE}${sos.photo_url}`} className="alert-image-thumb" alt="Distress flood preview" />
                        )}
                        <div className="alert-details">
                          <span className="alert-coords">Location: {sos.lat.toFixed(5)}, {sos.lng.toFixed(5)}</span>
                          <span>Water Level: {sos.detected_depth ? `${sos.detected_depth} cm` : 'Awaiting Gemini analysis...'}</span>
                          <span className="alert-meta">Log Time: {new Date(sos.timestamp).toLocaleTimeString()}</span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Tab 2: Decision support Chat */}
            {activeTab === 'chat' && (
              <div className="sidebar-chat">
                <div className="sidebar-chat-messages">
                  {chatMessages.map(m => (
                    <div key={m.id} className={`chat-message-wrapper ${m.role}`}>
                      <div className="chat-message-bubble">
                        {m.content}
                        {m.content.includes("###") && (
                          <div>
                            <button
                              className="download-report-btn"
                              onClick={() => handleDownloadReport(m.content)}
                            >
                              Download Markdown Briefing Report
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {isChatLoading && (
                    <div className="chat-message-wrapper ai">
                      <div className="chat-message-bubble" style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <span className="analysis-spinner"></span>
                        <span>Evaluating desilting & hydrologic changes...</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="chat-input-bar">
                  <input
                    type="text"
                    className="chat-text-input"
                    placeholder="Ask what-if queries or generate guidelines briefs..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendChat()}
                  />
                  <button className="chat-send-btn" onClick={handleSendChat}>Query</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
