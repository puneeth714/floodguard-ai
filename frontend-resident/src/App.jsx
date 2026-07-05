import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : window.location.protocol + '//' + window.location.hostname + ':8000';

// Coordinates to friendly name mapper (for fast local lookups)
const getFriendlyLocationName = (lat, lng) => {
  const latitude = parseFloat(lat).toFixed(4);
  const longitude = parseFloat(lng).toFixed(4);
  
  if (latitude === "12.9279" && longitude === "77.6271") {
    return "HSR Layout Sector 4 (Basin Hotspot)";
  }
  if (latitude === "12.9340" && longitude === "77.6320") {
    return "HSR Layout Sector 2 (Elevated)";
  }
  if (latitude === "12.9716" && longitude === "77.5946") {
    return "Bengaluru City Center (Fallback)";
  }
  return `GPS Area (${latitude}, ${longitude})`;
};

// Inline Markdown Parser to parse **bold** and Google Map URLs
const parseInlineMarkdown = (text) => {
  if (typeof text !== 'string') return text;
  
  const boldRegex = /\*\*([^*]+)\*\*/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = boldRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    parts.push(<strong key={match.index} style={{ color: 'var(--accent-cyan)', fontWeight: '600' }}>{match[1]}</strong>);
    lastIndex = boldRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.map((part, index) => {
    if (typeof part === 'string') {
      const mapLinkRegex = /(https:\/\/www\.google\.com\/maps\/dir\/[^\s\)]+)/g;
      const subparts = part.split(mapLinkRegex);
      return subparts.map((subpart, subindex) => {
        if (subpart.match(mapLinkRegex)) {
          return (
            <a key={`${index}-${subindex}`} href={subpart} target="_blank" rel="noopener noreferrer" className="safe-route-button">
              <svg className="route-icon" viewBox="0 0 24 24" style={{ width: '14px', height: '14px', marginRight: '6px', fill: 'currentColor' }}>
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
              </svg>
              Open Safe Detour Navigation
            </a>
          );
        }
        return subpart;
      });
    }
    return part;
  });
};

// Paragraph/Block Markdown Parser
const parseMarkdown = (text) => {
  if (!text) return '';
  
  const lines = text.split('\n');
  const elements = [];
  
  lines.forEach((line, i) => {
    const trimmed = line.trim();
    
    // Unordered lists
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      const content = trimmed.replace(/^[\*\-]\s+/, '');
      elements.push(
        <li key={i} style={{ marginLeft: '16px', marginBottom: '4px', listStyleType: 'disc' }}>
          {parseInlineMarkdown(content)}
        </li>
      );
      return;
    }
    
    // Ordered lists
    if (/^\d+\.\s+/.test(trimmed)) {
      const content = trimmed.replace(/^\d+\.\s+/, '');
      elements.push(
        <li key={i} style={{ marginLeft: '16px', marginBottom: '4px', listStyleType: 'decimal' }}>
          {parseInlineMarkdown(content)}
        </li>
      );
      return;
    }

    // Subheadings
    if (trimmed.startsWith('### ')) {
      const content = trimmed.replace(/^###\s+/, '');
      elements.push(
        <h4 key={i} style={{ color: 'var(--accent-orange)', margin: '12px 0 6px', fontWeight: '700', fontSize: '15px' }}>
          {parseInlineMarkdown(content)}
        </h4>
      );
      return;
    }
    if (trimmed.startsWith('## ')) {
      const content = trimmed.replace(/^##\s+/, '');
      elements.push(
        <h3 key={i} style={{ color: 'var(--accent-orange)', margin: '14px 0 8px', fontWeight: '700', fontSize: '17px' }}>
          {parseInlineMarkdown(content)}
        </h3>
      );
      return;
    }

    // Paragraph blocks or spacing
    if (trimmed === '') {
      elements.push(<div key={i} style={{ height: '6px' }} />);
    } else {
      elements.push(
        <p key={i} style={{ marginBottom: '6px' }}>
          {parseInlineMarkdown(line)}
        </p>
      );
    }
  });

  return <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>{elements}</div>;
};

function App() {
  const [profile, setProfile] = useState('rajesh');
  const [sessionId, setSessionId] = useState('');
  const [gpsCoords, setGpsCoords] = useState({ lat: 12.9279, lng: 77.6271 });
  const [resolvedAddress, setResolvedAddress] = useState('HSR Layout Sector 4 (Basin Hotspot)');
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [destination, setDestination] = useState('');

  // SOS Modal State
  const [isSosOpen, setIsSosOpen] = useState(false);
  const [sosPhoto, setSosPhoto] = useState(null);
  const [sosPreview, setSosPreview] = useState('');
  const [sosStage, setSosStage] = useState('upload'); // 'upload', 'sending', 'analyzing', 'done', 'error'
  const [sosTelemetry, setSosTelemetry] = useState({ lat: 0, lng: 0 });
  const [sosResult, setSosResult] = useState(null);
  
  // Custom distress inputs
  const [strandedCount, setStrandedCount] = useState(1);
  const [medicalNeeds, setMedicalNeeds] = useState('');
  const [activeSosId, setActiveSosId] = useState(null);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Helper to reverse geocode coordinate points asynchronously via backend
  const updateAddress = async (lat, lng, defaultName) => {
    try {
      const response = await fetch(`${API_BASE}/api/resident/reverse-geocode?latitude=${lat}&longitude=${lng}`);
      if (response.ok) {
        const data = await response.json();
        setResolvedAddress(data.formatted_address);
        return data.formatted_address;
      }
    } catch (e) {
      console.warn("Reverse geocoding request failed", e);
    }
    setResolvedAddress(defaultName);
    return defaultName;
  };

  // Initialize unique session on mount or profile change
  useEffect(() => {
    let newSessionId = `session_${profile}_${Math.random().toString(36).substr(2, 6)}`;
    if (profile === 'anonymous') {
      let anonId = localStorage.getItem('anonymous_uuid');
      if (!anonId) {
        anonId = 'anon_' + Math.random().toString(36).substr(2, 8);
        localStorage.setItem('anonymous_uuid', anonId);
      }
      newSessionId = `session_anonymous_${anonId}`;
    }
    setSessionId(newSessionId);
    setDestination('');

    // Load default coordinates based on profile
    if (profile === 'rajesh') {
      const coords = { lat: 12.9279, lng: 77.6271 };
      setGpsCoords(coords);
      const friendlyName = getFriendlyLocationName(coords.lat, coords.lng);
      setResolvedAddress(friendlyName);
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: `Hello Rajesh. Heavy rain is reported in your area. I have synchronized your location:\n**${friendlyName}**.\n\nLet me know if you need to check local risk status or find routes detour.`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } else if (profile === 'radha') {
      const coords = { lat: 12.9340, lng: 77.6320 };
      setGpsCoords(coords);
      const friendlyName = getFriendlyLocationName(coords.lat, coords.lng);
      setResolvedAddress(friendlyName);
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: `Hello Radha. I have synchronized your location:\n**${friendlyName}**.\n\nPlease ask any questions about nearby evacuation paths or storm risk.`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } else {
      // Anonymous / Real GPS mode
      setResolvedAddress('Locating...');
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: 'Locating your device... Please authorize GPS coordinates permission in your browser.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
      triggerBrowserGeolocation();
    }
  }, [profile]);

  // Subscribe to SSE stream for live bi-directional rescue status updates
  useEffect(() => {
    const sse = new EventSource(`${API_BASE}/api/official/live-sos-feed`);
    
    sse.addEventListener('update_sos', (event) => {
      const update = JSON.parse(event.data);
      const savedId = localStorage.getItem('active_sos_id');
      
      if (savedId && update.session_id === savedId) {
        setMessages(prev => {
          const bubbleId = `status_update_${update.status}_${update.timestamp}`;
          // Avoid duplicate appends
          if (prev.some(m => m.id === bubbleId)) return prev;
          
          return [
            ...prev,
            {
              id: bubbleId,
              role: 'assistant',
              content: `🚨 **Rescue Lifecycle Update**: Your distress alert status is now **${update.status.toUpperCase()}**.\n\n*   **Stranded Count**: ${update.stranded_people_count} stranded\n*   **Special Needs**: ${update.special_needs}\n*   **Water Level**: ${update.detected_depth} cm\n\nMunicipal Rescue dispatch teams have been updated.`,
              time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
          ];
        });
        
        if (update.status === 'resolved') {
          localStorage.removeItem('active_sos_id');
          setActiveSosId(null);
        }
      }
    });

    return () => {
      sse.close();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const triggerBrowserGeolocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const coords = {
            lat: parseFloat(position.coords.latitude.toFixed(6)),
            lng: parseFloat(position.coords.longitude.toFixed(6))
          };
          setGpsCoords(coords);
          const address = await updateAddress(coords.lat, coords.lng, `GPS Area (${coords.lat.toFixed(4)}, ${coords.lng.toFixed(4)})`);
          setMessages(prev => [
            ...prev.filter(m => m.id !== 'welcome'),
            {
              id: 'welcome_gps',
              role: 'assistant',
              content: `GPS telemetry synchronized successfully!\n\nLocation: **${address}**.\n\nHow can I help you check risk status or plan detours in this area?`,
              time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
          ]);
        },
        async (error) => {
          console.warn("Geolocation denied/failed, falling back to Bangalore center", error);
          const fallback = { lat: 12.9716, lng: 77.5946 };
          setGpsCoords(fallback);
          const address = await updateAddress(fallback.lat, fallback.lng, "Bengaluru City Center (Fallback)");
          setMessages(prev => [
            ...prev.filter(m => m.id !== 'welcome'),
            {
              id: 'welcome_fallback',
              role: 'assistant',
              content: `Location permissions denied. Loaded fallback area:\n**${address}**.\n\nHow can I assist you?`,
              time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
          ]);
        }
      );
    }
  };

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || inputText;
    if (!query.trim()) return;

    // Append user message
    const userMsg = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: query,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    // Auto-detect destination context (e.g. airport)
    let destParam = destination;
    if (query.toLowerCase().includes('airport')) {
      destParam = "13.1986,77.7066"; // KIA Airport coords
      setDestination(destParam);
    } else if (query.toLowerCase().includes('silk board')) {
      destParam = "12.9180,77.6271"; // Silk Board coords (using exact geocode_place mock to avoid mismatch)
      setDestination(destParam);
    }

    try {
      const response = await fetch(`${API_BASE}/api/resident/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          user_query: query,
          latitude: gpsCoords.lat,
          longitude: gpsCoords.lng,
          destination: destParam || null,
          demo_profile: profile,
          user_role: 'resident'
        })
      });

      if (!response.ok) throw new Error('API request failed');

      const data = await response.json();

      setMessages(prev => [
        ...prev,
        {
          id: `assistant_${Date.now()}`,
          role: 'assistant',
          content: data.final_response,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: 'assistant',
          content: 'Sorry, I encountered a communication error with the backend servers. Please try again.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // SOS photo selection
  const handlePhotoSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSosPhoto(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setSosPreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleOpenSos = () => {
    setSosPhoto(null);
    setSosPreview('');
    setSosResult(null);
    setSosStage('upload');
    setStrandedCount(1);
    setMedicalNeeds('');
    
    // Lock current telemetry coordinates for upload
    setSosTelemetry({ lat: gpsCoords.lat, lng: gpsCoords.lng });
    setIsSosOpen(true);
  };

  const handleSubmitSos = async () => {
    if (!sosPhoto) return;
    setSosStage('sending');

    const formData = new FormData();
    formData.append('file', sosPhoto);
    formData.append('latitude', sosTelemetry.lat);
    formData.append('longitude', sosTelemetry.lng);
    formData.append('stranded_count', strandedCount);
    formData.append('medical_needs', medicalNeeds || 'None');
    formData.append('user_query', 'Active resident flood SOS distress upload.');

    try {
      const response = await fetch(`${API_BASE}/api/resident/upload-sos`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('SOS upload failed');
      const data = await response.json();
      
      // Store session details to receive bi-directional SSE updates
      setActiveSosId(data.sos_id);
      localStorage.setItem('active_sos_id', data.sos_id);

      // Switch to analyzing stage
      setSosStage('analyzing');

      // Connect to Server Sent Events to wait for the vision analysis update
      const sse = new EventSource(`${API_BASE}/api/official/live-sos-feed`);
      
      sse.addEventListener('update_sos', (event) => {
        const update = JSON.parse(event.data);
        if (update.session_id === data.sos_id) {
          setSosResult({
            depth: update.detected_depth,
            severity: update.severity,
            desc: `Hazard depth evaluated at ${update.detected_depth} cm. Severity level marked as ${update.severity.toUpperCase()}. Emergency teams notified.`
          });
          setSosStage('done');
          sse.close();
        }
      });

      // Timeout safety check if analysis hangs
      setTimeout(() => {
        if (sosStage === 'analyzing') {
          setSosResult({
            depth: 35.0,
            severity: 'medium',
            desc: 'Water depth evaluation defaulted to 35cm (moderate risk). Distress signal broadcast complete.'
          });
          setSosStage('done');
          sse.close();
        }
      }, 8000);

    } catch (error) {
      console.error(error);
      setSosStage('error');
    }
  };

  return (
    <>
      {/* Header */}
      <header className="app-header glass-panel">
        <div className="logo-section">
          <span className="logo-icon">🛡️</span>
          <span className="logo-title">FloodGuard AI</span>
        </div>
        <div className="profile-selector-container">
          <span className="profile-label">Profile:</span>
          <select
            className="profile-select"
            value={profile}
            onChange={(e) => setProfile(e.target.value)}
          >
            <option value="rajesh">Rajesh (Sector 4)</option>
            <option value="radha">Radha (Sector 2)</option>
            <option value="anonymous">Anonymous (GPS)</option>
          </select>
        </div>
      </header>

      {/* Synchronized status bar showing resolved street address */}
      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '6px 16px', fontSize: '11px', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
        <span>Active Location:</span>
        <span style={{ color: 'var(--accent-cyan)', fontWeight: '600' }}>{resolvedAddress}</span>
      </div>

      {/* Chat Area */}
      <div className="chat-container">
        <div className="messages-list">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-wrapper ${msg.role}`}>
              <div className="message-bubble">
                {parseMarkdown(msg.content)}
              </div>
              <span className="message-time">{msg.time}</span>
            </div>
          ))}
          {isLoading && (
            <div className="message-wrapper assistant">
              <div className="message-bubble" style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span className="analysis-spinner"></span>
                <span>Calculating risk models...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Template Prompt chips */}
        <div className="templates-section">
          <p className="templates-title">Quick Actions</p>
          <div className="templates-list">
            <button
              className="template-chip"
              onClick={() => handleSendMessage("Am I safe in my place now?")}
            >
              🛡️ Am I safe in my place now?
            </button>
            <button
              className="template-chip"
              onClick={() => handleSendMessage("I want to go to the airport")}
            >
              ✈️ I want to go to airport
            </button>
            <button
              className="template-chip"
              onClick={() => handleSendMessage("Find nearby safe/shelter place for me")}
            >
              🏠 Find nearby safe/shelter place
            </button>
          </div>
        </div>

        {/* Bottom Input Area */}
        <div className="input-section">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask anything about local weather, risk or routes..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          />
          <button className="send-button" onClick={() => handleSendMessage()}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>

        {/* SOS Floating Action bar */}
        <div className="sos-trigger-container">
          <button className="sos-trigger-btn" onClick={handleOpenSos}>
            <span className="sos-indicator-pulse"></span>
            SUBMIT SOS ALERT
          </button>
        </div>
      </div>

      {/* SOS Modal Dialog */}
      {isSosOpen && (
        <div className="sos-modal-overlay glass-panel">
          <div className="sos-modal glass-panel">
            <div className="sos-modal-header">
              <span className="sos-modal-title">🚨 Flash Flood SOS Report</span>
              <button className="close-modal-btn" onClick={() => setIsSosOpen(false)}>×</button>
            </div>

            <div className="sos-telemetry-box">
              <div className="telemetry-row">
                <span className="telemetry-label">Signal Coordinates:</span>
                <span className="telemetry-value">{sosTelemetry.lat.toFixed(4)}, {sosTelemetry.lng.toFixed(4)}</span>
              </div>
              <div className="telemetry-row">
                <span className="telemetry-label">Approx Location:</span>
                <span className="telemetry-value" style={{ color: 'var(--accent-orange)' }}>{resolvedAddress}</span>
              </div>
              <div className="telemetry-row">
                <span className="telemetry-label">Status:</span>
                <span className="telemetry-value" style={{ color: '#ef4444' }}>TRANSMITTING</span>
              </div>
            </div>

            {sosStage === 'upload' && (
              <>
                <input
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  ref={fileInputRef}
                  onChange={handlePhotoSelect}
                />
                {sosPreview ? (
                  <img src={sosPreview} className="photo-preview" alt="Flood Preview" onClick={() => fileInputRef.current.click()} />
                ) : (
                  <div className="upload-zone" onClick={() => fileInputRef.current.click()}>
                    <div className="upload-icon">📸</div>
                    <p className="upload-text">Upload Flood Photo</p>
                    <p className="upload-subtext">Used by Gemini AI to estimate water depth</p>
                  </div>
                )}

                {/* Form fields for stranded count and special assistance */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%', margin: '10px 0', textAlign: 'left' }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Number of Stranded People:</label>
                  <input
                    type="number"
                    min="1"
                    value={strandedCount}
                    onChange={(e) => setStrandedCount(parseInt(e.target.value) || 1)}
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', padding: '8px', borderRadius: '4px', color: '#fff', fontSize: '13px' }}
                  />
                  
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Medical / Special Assistance Needs:</label>
                  <input
                    type="text"
                    placeholder="e.g. Elderly parents, Diabetic meds needed"
                    value={medicalNeeds}
                    onChange={(e) => setMedicalNeeds(e.target.value)}
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', padding: '8px', borderRadius: '4px', color: '#fff', fontSize: '13px' }}
                  />
                </div>

                <button
                  className="sos-action-btn"
                  disabled={!sosPhoto}
                  onClick={handleSubmitSos}
                >
                  Broadcast Distress Signal
                </button>
              </>
            )}

            {sosStage === 'sending' && (
              <div className="analysis-stage-container">
                <div className="analysis-stage-row">
                  <span className="analysis-spinner"></span>
                  <span>Uploading image to database server...</span>
                </div>
              </div>
            )}

            {sosStage === 'analyzing' && (
              <div className="analysis-stage-container">
                <div className="analysis-stage-row">
                  <span className="analysis-checkmark">✓</span>
                  <span>Distress signal registered in BigQuery.</span>
                </div>
                <div className="analysis-stage-row">
                  <span className="analysis-spinner"></span>
                  <span>Gemini Flash Vision evaluating flood depth...</span>
                </div>
              </div>
            )}

            {sosStage === 'done' && sosResult && (
              <>
                <div className="analysis-result-box">
                  <p className="analysis-result-title">SOS Broadcast Active!</p>
                  <p className="analysis-result-text">{sosResult.desc}</p>
                  <div className="evac-desc">
                    <strong>Calculated Water Depth:</strong> {sosResult.depth} cm<br />
                    <strong>Hazard Level:</strong> {sosResult.severity.toUpperCase()}
                  </div>
                </div>
                <button
                  className="sos-action-btn"
                  style={{ background: '#1e293b', marginTop: '16px' }}
                  onClick={() => setIsSosOpen(false)}
                >
                  Close Console
                </button>
              </>
            )}

            {sosStage === 'error' && (
              <div className="analysis-stage-container">
                <p style={{ color: 'var(--accent-red)', fontSize: '13px' }}>
                  Failed to transmit SOS signal. Please check your network and try again.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default App;
