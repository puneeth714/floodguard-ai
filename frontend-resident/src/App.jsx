import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = '';

const TRANSLATIONS = {
  en: {
    profile: "Profile",
    activeLocation: "Active Location",
    quickActions: "Quick Actions",
    askPlaceholder: "Ask anything about local weather, risk or routes...",
    submitSos: "SUBMIT SOS ALERT",
    strandedCount: "Number of Stranded People",
    specialNeeds: "Medical / Special Assistance Needs",
    broadcastSos: "Broadcast Distress Signal",
    areaStatus: "Your Area Status",
    liveUpdates: "LIVE UPDATES",
    progress: "Progress",
    voiceRecording: "Recording Voice...",
    voicePreview: "Voice Recorded (Send to Transcribe)",
    calculating: "Calculating risk models...",
    close: "Close Console",
    sosActive: "SOS Broadcast Active!",
    uploadPhoto: "Upload Flood Photo",
    geminiVision: "Used by Gemini AI to estimate water depth",
    signalRegistered: "Distress signal registered in BigQuery.",
    geminiEvaluating: "Gemini Flash Vision evaluating flood depth...",
    uploadingDb: "Uploading image to database server...",
    safeDirections: "Open Safe Detour Navigation",
    getDirections: "Get Directions",
    liveBulletins: "Live Status bulletins",
    evacShelters: "Evacuation Shelters Nearby",
    pathfinder: "Route Pathfinder",
    blockedRoads: "Blocked Roads Detected",
    origin: "Origin",
    detour: "Detour",
    destination: "Destination",
    fviHeader: "Flood Vulnerability Index (FVI)",
    riskAssess: "FVI Risk Assessment"
  },
  kn: {
    profile: "ಪ್ರೊಫೈಲ್",
    activeLocation: "ಸಕ್ರಿಯ ಸ್ಥಳ",
    quickActions: "ತ್ವರಿತ ಕ್ರಿಯೆಗಳು",
    askPlaceholder: "ಸ್ಥಳೀಯ ಹವಾಮಾನ, ಅಪಾಯ ಅಥವಾ ಮಾರ್ಗಗಳ ಬಗ್ಗೆ ಕೇಳಿ...",
    submitSos: "SOS ಎಚ್ಚರಿಕೆ ಕಳುಹಿಸಿ",
    strandedCount: "ಸಿಲುಕಿರುವ ಜನರ ಸಂಖ್ಯೆ",
    specialNeeds: "ವೈದ್ಯಕೀಯ / ವಿಶೇಷ ಸಹಾಯದ ಅಗತ್ಯಗಳು",
    broadcastSos: "ತುರ್ತು ಸಂಕೇತ ಪ್ರಸಾರ ಮಾಡಿ",
    areaStatus: "ನಿಮ್ಮ ಪ್ರದೇಶದ ಸ್ಥಿತಿ",
    liveUpdates: "ಲೈವ್ ಅಪ್‌ಡೇಟ್‌ಗಳು",
    progress: "ಪ್ರಗತಿ",
    voiceRecording: "ಧ್ವನಿ ರೆಕಾರ್ಡಿಂಗ್...",
    voicePreview: "ಧ್ವನಿ ರೆಕಾರ್ಡ್ ಆಗಿದೆ (ಕಳುಹಿಸಿ)",
    calculating: "ಅಪಾಯದ ಮಾದರಿಗಳನ್ನು ಲೆಕ್ಕಹಾಕಲಾಗುತ್ತಿದೆ...",
    close: "ಮುಚ್ಚಿ",
    sosActive: "SOS ತುರ್ತು ಪ್ರಸಾರ ಸಕ್ರಿಯವಾಗಿದೆ!",
    uploadPhoto: "ಪ್ರವಾಹದ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
    geminiVision: "ನೀರಿನ ಆಳವನ್ನು ಅಂದಾಜು ಮಾಡಲು ಜೆಮಿನಿ AI ಬಳಸುತ್ತದೆ",
    signalRegistered: "ತುರ್ತು ಸಂಕೇತ ಬಿಗ್‌ಕ್ವೆರಿಯಲ್ಲಿ ದಾಖಲಾಗಿದೆ.",
    geminiEvaluating: "ಜೆಮಿನಿ ಫ್ಲ್ಯಾಶ್ ವಿಷನ್ ನೀರಿನ ಆಳ ಅಂದಾಜು ಮಾಡುತ್ತಿದೆ...",
    uploadingDb: "ಚಿತ್ರವನ್ನು ಸರ್ವರ್‌ಗೆ ಅಪ್‌ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...",
    safeDirections: "ಸುರಕ್ಷಿತ ಮಾರ್ಗ ನಕ್ಷೆ ತೆರೆಯಿರಿ",
    getDirections: "ಮಾರ್ಗಸೂಚಿ ಪಡೆಯಿರಿ",
    liveBulletins: "ಲೈವ್ ಸ್ಥಿತಿ ಬುಲೆಟಿನ್‌ಗಳು",
    evacShelters: "ಹತ್ತಿರದ ಆಶ್ರಯ ತಾಣಗಳು",
    pathfinder: "ಪರ್ಯಾಯ ಮಾರ್ಗ ಶೋಧಕ",
    blockedRoads: "ನಿರ್ಬಂಧಿಸಲಾದ ರಸ್ತೆಗಳು",
    origin: "ಪ್ರಾರಂಭದ ಸ್ಥಳ",
    detour: "ಪರ್ಯಾಯ ಮಾರ್ಗ",
    destination: "ತಲುಪಬೇಕಾದ ಸ್ಥಳ",
    fviHeader: "ಪ್ರವಾಹ ಸೂಕ್ಷ್ಮತೆಯ ಸೂಚ್ಯಂಕ (FVI)",
    riskAssess: "FVI ಅಪಾಯದ ಮೌಲ್ಯಮಾಪನ"
  },
  hi: {
    profile: "प्रोफ़ाइल",
    activeLocation: "सक्रिय स्थान",
    quickActions: "त्वरित कार्रवाई",
    askPlaceholder: "स्थानीय मौसम, जोखिम या मार्गों के बारे में पूछें...",
    submitSos: "SOS अलर्ट भेजें",
    strandedCount: "फंसे हुए लोगों की संख्या",
    specialNeeds: "चिकित्सा / विशेष सहायता की आवश्यकताएं",
    broadcastSos: "आपातकालीन संकेत प्रसारित करें",
    areaStatus: "आपके क्षेत्र की स्थिति",
    liveUpdates: "लाइव अपडेट",
    progress: "प्रगति",
    voiceRecording: "आवाज रिकॉर्ड हो रही है...",
    voicePreview: "आवाज रिकॉर्ड की गई (भेजें)",
    calculating: "जोखिम मॉडल की गणना...",
    close: "बंद करें",
    sosActive: "SOS प्रसारण सक्रिय है!",
    uploadPhoto: "बाढ़ की फोटो अपलोड करें",
    geminiVision: "पानी की गहराई का अनुमान लगाने के लिए जेमिनी AI द्वारा उपयोग किया जाता है",
    signalRegistered: "संकट संकेत बिगक्वेरी में पंजीकृत किया गया।",
    geminiEvaluating: "जेमिनी फ्लैश विजन बाढ़ की गहराई का मूल्यांकन कर रहा है...",
    uploadingDb: "सर्वर पर छवि अपलोड की जा रही है...",
    safeDirections: "सुरक्षित मार्ग नेविगेशन खोलें",
    getDirections: "दिशा-निर्देश प्राप्त करें",
    liveBulletins: "लाइव स्थिति बुलेटिन",
    evacShelters: "आसपास के निकासी आश्रय",
    pathfinder: "मार्ग खोजक",
    blockedRoads: "अवरुद्ध सड़कें",
    origin: "मूल स्थान",
    detour: "विपथन",
    destination: "गंतव्य",
    fviHeader: "बाढ़ संवेदनशीलता सूचकांक (FVI)",
    riskAssess: "FVI जोखिम मूल्यांकन"
  },
  te: {
    profile: "ప్రొఫైల్",
    activeLocation: "సక్రియ స్థానం",
    quickActions: "శీఘ్ర చర్యలు",
    askPlaceholder: "స్థానిక వాతావరణం, ప్రమాదం లేదా మార్గాల గురించి అడగండి...",
    submitSos: "SOS అలర్ట్ పంపండి",
    strandedCount: "చిక్కుకున్న వ్యక్తుల సంఖ్య",
    specialNeeds: "వైద్య / ప్రత్యేక సహాయ అవసరాలు",
    broadcastSos: "ఆపద సిగ్నల్ ప్రసారం చేయి",
    areaStatus: "మీ ప్రాంతం పరిస్థితి",
    liveUpdates: "లైవ్ అప్డేట్లు",
    progress: "ప్రగతి",
    voiceRecording: "వాయిస్ రికార్డింగ్...",
    voicePreview: "వాయిస్ రికార్డ్ చేయబడింది (పంపించు)",
    calculating: "ప్రమాద నమూనాల లెక్కింపు...",
    close: "మూసివేయి",
    sosActive: "SOS సిగ్నల్ క్రియాశీలంగా ఉంది!",
    uploadPhoto: "వరద ఫోటోను అప్‌లోడ్ చేయండి",
    geminiVision: "నీటి లోతును అంచనా వేయడానికి జెమిని AI ఉపయోగిస్తుంది",
    signalRegistered: "ఆపద సిగ్నల్ బిగ్‌క్వారీలో నమోదు చేయబడింది.",
    geminiEvaluating: "జెమిని ఫ్లాష్ విజన్ వరద లోతును అంచనా వేస్తోంది...",
    uploadingDb: "సర్వర్‌కు చిత్రాన్ని అప్‌లోడ్ చేస్తోంది...",
    safeDirections: "సురక్షిత ప్రత్యామ్నాయ నావిగేషన్ తెరువు",
    getDirections: "దిశలను పొందండి",
    liveBulletins: "లైవ్ అప్‌డేట్ బులెటిన్లు",
    evacShelters: "సమీప సహాయ శిబిరాలు",
    pathfinder: "ప్రత్యామ్నాయ మార్గ శోధన",
    blockedRoads: "బ్లాక్ చేయబడిన రహదారులు",
    origin: "ప్రారంభ స్థానం",
    detour: "డెటూర్",
    destination: "గమ్యస్థానం",
    fviHeader: "వరద నష్ట సూచిక (FVI)",
    riskAssess: "FVI ప్రమాద అంచనా"
  }
};

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
    parts.push(<strong key={match.index} style={{ color: 'var(--accent-blue)', fontWeight: '600' }}>{match[1]}</strong>);
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

// --------------------------------------------------------------------------- #
// Custom Interactive Widgets
// --------------------------------------------------------------------------- #

function FviGaugeWidget({ data, language }) {
  const score = data.score;
  const severity = data.severity || "low";
  const telemetry = data.telemetry || {};
  
  let colorClass = "safe";
  if (score > 10 && score <= 20) colorClass = "warning-light";
  else if (score > 20 && score <= 30) colorClass = "warning-orange";
  else if (score > 30) colorClass = "danger";

  return (
    <div className={`widget-card fvi-card ${colorClass}`}>
      <div className="widget-header">
        <span>📊 {TRANSLATIONS[language].fviHeader}</span>
        <span className={`badge ${colorClass}`}>{severity.toUpperCase()} RISK</span>
      </div>
      <div className="gauge-container">
        <div className="gauge-bar-bg">
          <div className={`gauge-bar-fill ${colorClass}`} style={{ width: `${Math.min(100, (score / 40) * 100)}%` }}></div>
        </div>
        <div className="gauge-score-label">FVI Score: <strong>{score.toFixed(2)}</strong> / 40.00</div>
      </div>
      <div className="telemetry-grid">
        <div className="telemetry-item">
          <span className="telemetry-icon">⛰️</span>
          <span className="telemetry-label">Elevation</span>
          <span className="telemetry-value">{telemetry.elevation || 'N/A'}</span>
        </div>
        <div className="telemetry-item">
          <span className="telemetry-icon">⛈️</span>
          <span className="telemetry-label">Rain Rate</span>
          <span className="telemetry-value">{telemetry.precipitation || 'N/A'}</span>
        </div>
        <div className="telemetry-item">
          <span className="telemetry-icon">📈</span>
          <span className="telemetry-label">Slope</span>
          <span className="telemetry-value">{telemetry.slope || 'N/A'}</span>
        </div>
        <div className="telemetry-item">
          <span className="telemetry-icon">🚰</span>
          <span className="telemetry-label">Drain Dist</span>
          <span className="telemetry-value">{telemetry.drain_distance || 'N/A'}</span>
        </div>
      </div>
    </div>
  );
}

function DetourRouteWidget({ data, language }) {
  const origin = data.origin_name;
  const destination = data.destination_name;
  const blockages = data.blockage_points || [];
  const detour = data.waypoint_address;
  const mapsUrl = data.maps_url;

  return (
    <div className="widget-card route-card">
      <div className="widget-header">
        <span>🚗 {TRANSLATIONS[language].pathfinder}</span>
      </div>
      <div className="route-path">
        <div className="route-point">
          <span className="dot start"></span>
          <span>{TRANSLATIONS[language].origin}: <strong>{origin}</strong></span>
        </div>
        {blockages.length > 0 && (
          <div className="route-blockages">
            <p className="blockage-title">🚫 {TRANSLATIONS[language].blockedRoads}:</p>
            <ul>
              {blockages.map((b, i) => <li key={i}>{b}</li>)}
            </ul>
          </div>
        )}
        {detour && (
          <div className="route-point detour">
            <span className="dot detour-dot"></span>
            <span>{TRANSLATIONS[language].detour}: <strong style={{ color: 'var(--accent-orange)' }}>{detour}</strong></span>
          </div>
        )}
        <div className="route-point end">
          <span className="dot destination"></span>
          <span>{TRANSLATIONS[language].destination}: <strong>{destination}</strong></span>
        </div>
      </div>
      <a href={mapsUrl} target="_blank" rel="noopener noreferrer" className="safe-route-button clickable">
        <svg className="route-icon" viewBox="0 0 24 24" style={{ width: '16px', height: '16px', marginRight: '6px', fill: 'currentColor' }}>
          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
        </svg>
        {TRANSLATIONS[language].safeDirections}
      </a>
    </div>
  );
}

function ShelterListWidget({ data, language }) {
  const shelters = data.shelters || [];
  const [expandedIndex, setExpandedIndex] = useState(null);

  return (
    <div className="widget-card shelter-card">
      <div className="widget-header">
        <span>🏠 {TRANSLATIONS[language].evacShelters}</span>
      </div>
      <div className="shelter-list">
        {shelters.map((s, idx) => {
          let statusClass = "safe";
          if (s.status === "near_full") statusClass = "warning-light";
          else if (s.status === "full" || s.status === "closed") statusClass = "danger";

          return (
            <div 
              key={idx} 
              className="shelter-item"
              onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
              style={{ cursor: 'pointer' }}
            >
              <div className="shelter-summary">
                <div>
                  <p className="shelter-name">{s.name}</p>
                  <p className="shelter-dist">📍 {s.distance}</p>
                </div>
                <span className={`badge ${statusClass}`}>
                  {s.status.toUpperCase()} ({s.occupancy_rate})
                </span>
              </div>
              {expandedIndex === idx && (
                <div className="shelter-details" style={{ marginTop: '10px', padding: '8px 0', borderTop: '1px solid rgba(0,0,0,0.06)' }}>
                  <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                    Operating under local disaster administration. Equipped with basic dry rations, water, and first aid supplies.
                  </p>
                  <a href={s.directions_url} target="_blank" rel="noopener noreferrer" className="shelter-route-btn clickable">
                    {TRANSLATIONS[language].getDirections}
                  </a>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatusBulletinsWidget({ data, language }) {
  const bulletins = data.bulletins || [];
  const iconMap = {
    car: "🚗",
    train: "🚆",
    ban: "🚫",
    cloud: "⛈️",
    phone: "📞"
  };

  return (
    <div className="widget-card bulletins-card">
      <div className="widget-header">
        <span>📢 {TRANSLATIONS[language].liveBulletins}</span>
      </div>
      <div className="bulletins-list">
        {bulletins.map((b, i) => {
          let colorClass = "safe";
          if (b.alert_type === "warning") colorClass = "warning-light";
          else if (b.alert_type === "danger") colorClass = "danger";

          return (
            <div key={i} className={`bulletin-item ${colorClass}`}>
              <span className="bulletin-icon">{iconMap[b.icon] || "ℹ️"}</span>
              <span className="bulletin-text">{b.text}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SosTrackerWidget({ data }) {
  const sosId = data.sos_id;
  const stages = data.stages || [];

  return (
    <div className="widget-card tracker-card">
      <div className="widget-header">
        <span>🚨 SOS Distress Tracker</span>
        <span className="sos-id-label">{sosId}</span>
      </div>
      <div className="tracker-timeline">
        {stages.map((st, i) => {
          let statusClass = "pending";
          if (st.status === "completed") statusClass = "completed";
          else if (st.status === "active") statusClass = "active";

          return (
            <div key={i} className={`timeline-stage ${statusClass}`}>
              <div className="timeline-node">
                {st.status === "completed" ? "✓" : i + 1}
              </div>
              <div className="timeline-content">
                <p className="stage-name">{st.name}</p>
                {st.details && <p className="stage-details">{st.details}</p>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function WeatherForecastWidget({ data }) {
  const rain = data.precipitation_forecast;
  const tideHeight = data.tide_height;
  const tideTime = data.tide_time;
  const advice = data.advice;

  return (
    <div className="widget-card weather-card">
      <div className="widget-header">
        <span>⛈️ Storm & High Tide Forecast</span>
      </div>
      <div className="weather-grid">
        <div className="weather-stat">
          <span className="weather-stat-label">RAIN OUTLOOK</span>
          <span className="weather-stat-val">{rain}</span>
        </div>
        {tideHeight && (
          <div className="weather-stat">
            <span className="weather-stat-label">HIGH TIDE</span>
            <span className="weather-stat-val">{tideHeight} at {tideTime}</span>
          </div>
        )}
      </div>
      {advice && (
        <div className="weather-advice">
          <span className="advice-icon">⚠️</span>
          <p className="advice-text">{advice}</p>
        </div>
      )}
    </div>
  );
}

const renderWidget = (widget, language) => {
  if (!widget || !widget.type) return null;
  switch (widget.type) {
    case 'fvi_gauge':
      return <FviGaugeWidget data={widget.data} language={language} />;
    case 'detour_route':
      return <DetourRouteWidget data={widget.data} language={language} />;
    case 'shelter_list':
      return <ShelterListWidget data={widget.data} language={language} />;
    case 'status_bulletins':
      return <StatusBulletinsWidget data={widget.data} language={language} />;
    case 'sos_tracker':
      return <SosTrackerWidget data={widget.data} />;
    case 'weather_forecast':
      return <WeatherForecastWidget data={widget.data} />;
    default:
      return null;
  }
};

const renderMessageContent = (msg, language) => {
  if (!msg.content) return '';
  if (typeof msg.content === 'string') {
    return parseMarkdown(msg.content);
  }
  
  const data = msg.content;
  return (
    <div className="structured-content">
      <div className="conversational-response">
        {parseMarkdown(data.final_response)}
      </div>
      {data.widgets && data.widgets.length > 0 && (
        <div className="widgets-list">
          {data.widgets.map((widget, idx) => (
            <div key={idx} className="widget-wrapper">
              {renderWidget(widget, language)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// --------------------------------------------------------------------------- #
// Mock Default Area Status cards (aligned to Profiles)
// --------------------------------------------------------------------------- #

const defaultAlertRajesh = {
  level: "warning",
  title: "Orange Alert",
  description: "Moderate waterlogging reported in Milan Subway. High tide expected in 45 mins.",
  metrics: [
    { label: "RAIN (24H)", value: "112 mm" },
    { label: "HIGH TIDE", value: "4.1m (14:15)" },
    { label: "NDRF NEAREST", value: "2.4 km" }
  ]
};

const defaultAlertRadha = {
  level: "safe",
  title: "Green Alert",
  description: "No active waterlogging reported in Sector 2 basin. Elevated terrain.",
  metrics: [
    { label: "RAIN (24H)", value: "22 mm" },
    { label: "ELEVATION", value: "858m (High)" },
    { label: "DRY OUTLOOK", value: "Active" }
  ]
};

// --------------------------------------------------------------------------- #
// App Component
// --------------------------------------------------------------------------- #

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

  // New features state
  const [language, setLanguage] = useState('en');
  const [activeAreaAlert, setActiveAreaAlert] = useState(defaultAlertRajesh);

  // Voice recording states
  const [recordingState, setRecordingState] = useState('idle'); // 'idle', 'recording', 'preview'
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioUrl, setAudioUrl] = useState('');
  const [audioBlob, setAudioBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [timerIntervalId, setTimerIntervalId] = useState(null);

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

    // Load default coordinates and alert states based on profile
    if (profile === 'rajesh') {
      const coords = { lat: 12.9279, lng: 77.6271 };
      setGpsCoords(coords);
      const friendlyName = getFriendlyLocationName(coords.lat, coords.lng);
      setResolvedAddress(friendlyName);
      setActiveAreaAlert(defaultAlertRajesh);
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
      setActiveAreaAlert(defaultAlertRadha);
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
      setActiveAreaAlert(null);
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
              content: {
                final_response: `Your rescue alert status is now **${update.status.toUpperCase()}**.`,
                widgets: [
                  {
                    type: "sos_tracker",
                    data: {
                      sos_id: update.session_id,
                      stages: [
                        { name: "Signal Registered", status: "completed", details: "Logged successfully" },
                        { name: "Vision Analysis", status: "completed", details: `Water level estimated: ${update.detected_depth} cm` },
                        { name: "Rescue Status", status: update.status === 'resolved' ? "completed" : "active", details: `Status: ${update.status.toUpperCase()} (${update.special_needs})` },
                        { name: "Resolved", status: update.status === 'resolved' ? "completed" : "pending" }
                      ]
                    }
                  }
                ]
              },
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
      const response = await fetch(`${API_BASE}/api/resident/chat?stream=true`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          user_query: query,
          latitude: gpsCoords.lat,
          longitude: gpsCoords.lng,
          destination: destParam || null,
          demo_profile: profile,
          user_role: 'resident',
          language: language
        })
      });

      if (!response.ok) throw new Error('API request failed');

      const tempId = `temp_${Date.now()}`;
      setMessages(prev => [
        ...prev,
        {
          id: tempId,
          role: 'assistant',
          content: '⏳ Preparing ADK agent session...',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Save partial line

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const payload = JSON.parse(line.substring(6));
              if (payload.type === 'status' || payload.type === 'tool') {
                setMessages(prev => prev.map(m => m.id === tempId ? { ...m, content: `⚙️ **${TRANSLATIONS[language].progress}**: *${payload.content}*` } : m));
              } else if (payload.type === 'final') {
                const parsedContent = payload.content;
                
                // Update global alert if provided in response
                if (parsedContent.status_alert) {
                  setActiveAreaAlert(parsedContent.status_alert);
                }

                setMessages(prev => prev.map(m => m.id === tempId ? {
                  ...m,
                  id: `assistant_${Date.now()}`,
                  content: parsedContent
                } : m));
              }
            } catch (e) {
              console.warn("Parse stream chunk error:", e);
            }
          }
        }
      }
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

  // Voice recording triggers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        setAudioBlob(blob);
        setAudioUrl(url);
        setRecordingState('preview');
        stream.getTracks().forEach(track => track.stop());
      };

      setAudioChunks(chunks);
      setMediaRecorder(recorder);
      recorder.start();
      setRecordingState('recording');
      setRecordingTime(0);
      
      const interval = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      setTimerIntervalId(interval);
    } catch (e) {
      console.error("Audio recording permission denied or failed", e);
      alert("Microphone permission denied or unsupported by browser.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && recordingState === 'recording') {
      mediaRecorder.stop();
      if (timerIntervalId) {
        clearInterval(timerIntervalId);
        setTimerIntervalId(null);
      }
    }
  };

  const cancelRecording = () => {
    if (mediaRecorder && recordingState === 'recording') {
      mediaRecorder.stop();
    }
    if (timerIntervalId) {
      clearInterval(timerIntervalId);
      setTimerIntervalId(null);
    }
    setRecordingState('idle');
    setAudioBlob(null);
    setAudioUrl('');
  };

  const handleSendVoice = async () => {
    if (!audioBlob) return;
    setIsLoading(true);
    setRecordingState('idle');
    
    const formData = new FormData();
    formData.append('file', audioBlob, 'voice_query.webm');

    try {
      const transcribeResponse = await fetch(`${API_BASE}/api/resident/voice-to-text`, {
        method: 'POST',
        body: formData
      });

      if (!transcribeResponse.ok) throw new Error("Transcription failed");
      const transcribeData = await transcribeResponse.json();
      const transcriptText = transcribeData.transcript;

      if (transcriptText.trim()) {
        await handleSendMessage(transcriptText);
      } else {
        alert("Could not detect any speech. Please record again.");
      }
    } catch (err) {
      console.error("Voice dispatch error:", err);
      alert("Failed to transcribe audio.");
    } finally {
      setIsLoading(false);
      setAudioBlob(null);
      setAudioUrl('');
    }
  };

  const [audioChunks, setAudioChunks] = useState([]);

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
      <header className="app-header">
        <div className="logo-section">
          <span className="logo-icon">💧</span>
          <span className="logo-title">FloodGuard</span>
        </div>
        <div className="header-controls">
          {/* Language Selector */}
          <div className="control-group">
            <select
              className="control-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="en">English (EN)</option>
              <option value="kn">ಕನ್ನಡ (KN)</option>
              <option value="hi">हिन्दी (HI)</option>
              <option value="te">తెలుగు (TE)</option>
            </select>
          </div>
          {/* Profile Switcher */}
          <div className="control-group">
            <select
              className="control-select"
              value={profile}
              onChange={(e) => setProfile(e.target.value)}
            >
              <option value="rajesh">Rajesh (Sector 4)</option>
              <option value="radha">Radha (Sector 2)</option>
              <option value="anonymous">Anonymous (GPS)</option>
            </select>
          </div>
          <button className="header-sos-btn" onClick={handleOpenSos}>SOS</button>
        </div>
      </header>

      {/* Synchronized location info bar */}
      <div className="location-bar">
        <i className="location-icon">📍</i>
        <span className="location-val">{resolvedAddress}</span>
      </div>

      {/* Global Area Status Alert Banner (dynamic according to profile location FVI check) */}
      {activeAreaAlert && (
        <section className="p-4" style={{ paddingBottom: '0px' }}>
          <div className={`area-status-card ${activeAreaAlert.level}-gradient`}>
            <div className="alert-top">
              <div>
                <p className="alert-sub">{TRANSLATIONS[language].areaStatus}</p>
                <h2 className="alert-title">{activeAreaAlert.title}</h2>
              </div>
              <div className="alert-icon-box">
                <i className="fas fa-cloud-showers-heavy"></i>
              </div>
            </div>
            <p className="alert-desc">
              {activeAreaAlert.description}
            </p>
            {activeAreaAlert.metrics && activeAreaAlert.metrics.length > 0 && (
              <div className="alert-metrics">
                {activeAreaAlert.metrics.map((m, idx) => (
                  <div key={idx} className="metric-item">
                    <p className="metric-lbl">{m.label}</p>
                    <p className="metric-val">{m.value}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Main Chat Area segment */}
      <section className="chat-container">
        <div className="chat-header-meta">
          <h3 className="ai-assistant-label">Sahas AI Assistant</h3>
          <span className="live-badge">
            <span className="live-dot"></span> {TRANSLATIONS[language].liveUpdates}
          </span>
        </div>

        <div className="messages-list">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-wrapper ${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="avatar-box">🤖</div>
              )}
              <div className={`message-bubble ${msg.role === 'assistant' ? 'ai' : 'user'}`}>
                {renderMessageContent(msg, language)}
              </div>
              <span className="message-time">{msg.time}</span>
            </div>
          ))}
          {isLoading && (
            <div className="message-wrapper assistant">
              <div className="avatar-box">🤖</div>
              <div className="message-bubble ai" style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span className="analysis-spinner"></span>
                <span>{TRANSLATIONS[language].calculating}</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Action input composition controls */}
        <div className="composer-bar">
          {/* Suggested Quick action chips */}
          <div className="suggestions-row">
            <button
              className="suggestion-pill"
              onClick={() => handleSendMessage(language === 'en' ? "Am I safe in my place now?" : "ನನ್ನ ಪ್ರದೇಶ ಸುರಕ್ಷಿತವೇ?")}
            >
              🛡️ {language === 'en' ? "Is my area safe?" : "ನನ್ನ ಪ್ರದೇಶ ಸುರಕ್ಷಿತವೇ?"}
            </button>
            <button
              className="suggestion-pill"
              onClick={() => handleSendMessage(language === 'en' ? "Find shelters near me" : "ಹತ್ತಿರದ ಆಶ್ರಯ ತಾಣಗಳು")}
            >
              🏠 {language === 'en' ? "Shelters near me" : "ಹತ್ತಿರದ ಆಶ್ರಯ ತಾಣಗಳು"}
            </button>
            <button
              className="suggestion-pill"
              onClick={() => handleSendMessage(language === 'en' ? "Is it safe to drive to the airport?" : "ವಿಮಾನ ನಿಲ್ದಾಣದ ಮಾರ್ಗ")}
            >
              ✈️ {language === 'en' ? "Airport Route Check" : "ವಿಮಾನ ನಿಲ್ದಾಣದ ಮಾರ್ಗ"}
            </button>
          </div>

          {/* Voice active recording overlay UI if active */}
          {recordingState === 'recording' && (
            <div className="voice-recording-overlay">
              <div className="recording-equalizer">
                <span className="bar-pulsing"></span>
                <span className="bar-pulsing delay-1"></span>
                <span className="bar-pulsing delay-2"></span>
                <span className="bar-pulsing delay-3"></span>
              </div>
              <span className="voice-record-text">{TRANSLATIONS[language].voiceRecording} ({recordingTime}s)</span>
              <div className="voice-record-controls">
                <button className="voice-cancel-btn" onClick={cancelRecording}>✕</button>
                <button className="voice-stop-btn" onClick={stopRecording}>⏹ Stop</button>
              </div>
            </div>
          )}

          {/* Voice preview state UI */}
          {recordingState === 'preview' && (
            <div className="voice-preview-overlay">
              <span className="voice-record-text">🎙️ {TRANSLATIONS[language].voicePreview}</span>
              <audio src={audioUrl} controls className="mini-audio-player" />
              <div className="voice-record-controls">
                <button className="voice-cancel-btn" onClick={cancelRecording}>✕ Trash</button>
                <button className="voice-send-btn" onClick={handleSendVoice}>Send Query</button>
              </div>
            </div>
          )}

          {recordingState === 'idle' && (
            <div className="input-row">
              <button className="camera-btn" onClick={handleOpenSos}>
                📷
              </button>
              <button className="mic-btn" onClick={startRecording}>
                🎙️
              </button>
              <div className="input-field-container">
                <input
                  type="text"
                  className="chat-input"
                  placeholder={TRANSLATIONS[language].askPlaceholder}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <button className="send-button" onClick={() => handleSendMessage()}>
                  ➔
                </button>
              </div>
            </div>
          )}

          {/* Bottom Tabs navigation layout */}
          <div className="bottom-tabs">
            <button className="tab-item active">
              🏠
              <span>Home</span>
            </button>
            <button className="tab-item" onClick={() => alert("Official Command Map is accessible via official dashboard.")}>
              🗺️
              <span>Flood Map</span>
            </button>
            <button className="tab-item" onClick={handleOpenSos}>
              📢
              <span>Report</span>
            </button>
            <button className="tab-item" onClick={() => alert("Helpline numbers: 112 (Disaster Mgmt), 108 (Medical)")}>
              📞
              <span>Helpline</span>
            </button>
          </div>
        </div>
      </section>

      {/* SOS Modal Dialog */}
      {isSosOpen && (
        <div className="sos-modal-overlay">
          <div className="sos-modal">
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
                    <p className="upload-text">{TRANSLATIONS[language].uploadPhoto}</p>
                    <p className="upload-subtext">{TRANSLATIONS[language].geminiVision}</p>
                  </div>
                )}

                <div className="sos-form-fields">
                  <label>{TRANSLATIONS[language].strandedCount}:</label>
                  <input
                    type="number"
                    min="1"
                    className="form-input"
                    value={strandedCount}
                    onChange={(e) => setStrandedCount(parseInt(e.target.value) || 1)}
                  />
                  
                  <label>{TRANSLATIONS[language].specialNeeds}:</label>
                  <input
                    type="text"
                    placeholder="e.g. Elderly parents, Insulin medication"
                    className="form-input"
                    value={medicalNeeds}
                    onChange={(e) => setMedicalNeeds(e.target.value)}
                  />
                </div>

                <button
                  className="sos-action-btn"
                  disabled={!sosPhoto}
                  onClick={handleSubmitSos}
                >
                  {TRANSLATIONS[language].broadcastSos}
                </button>
              </>
            )}

            {sosStage === 'sending' && (
              <div className="analysis-stage-container">
                <div className="analysis-stage-row">
                  <span className="analysis-spinner"></span>
                  <span>{TRANSLATIONS[language].uploadingDb}</span>
                </div>
              </div>
            )}

            {sosStage === 'analyzing' && (
              <div className="analysis-stage-container">
                <div className="analysis-stage-row">
                  <span className="analysis-checkmark">✓</span>
                  <span>{TRANSLATIONS[language].signalRegistered}</span>
                </div>
                <div className="analysis-stage-row">
                  <span className="analysis-spinner"></span>
                  <span>{TRANSLATIONS[language].geminiEvaluating}</span>
                </div>
              </div>
            )}

            {sosStage === 'done' && sosResult && (
              <>
                <div className="analysis-result-box">
                  <p className="analysis-result-title">{TRANSLATIONS[language].sosActive}</p>
                  <p className="analysis-result-text">{sosResult.desc}</p>
                  <div className="evac-desc">
                    <strong>Calculated Water Depth:</strong> {sosResult.depth} cm<br />
                    <strong>Hazard Level:</strong> {sosResult.severity.toUpperCase()}
                  </div>
                </div>
                <button
                  className="sos-action-btn close-action-btn"
                  onClick={() => setIsSosOpen(false)}
                >
                  {TRANSLATIONS[language].close}
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
