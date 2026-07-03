# Hackathon Prototype: Demo Constraints & Design Assumptions

This document outlines the specific demo constraints, mock parameters, and architectural assumptions implemented for **FloodGuard AI** during the GenAI APAC Hackathon. These boundaries ensure a flawless, low-latency live demonstration while showcasing high-value enterprise features.

---

## 1. Resident Persona Profiles (Authentication Bypass)
* **Constraint**: No actual user signup, authentication, or phone verification screens are implemented.
* **Implementation**: The Resident App features a **Demo Profile Selector** in the header. Judges/presenters can switch between:
  1. **Rajesh**: Hardcoded to a residential address in HSR Layout Sector 4 ($12.9279^\circ \text{N}, 77.6271^\circ \text{E}$). Used to show the *Prevention Phase* (checklist generation) and *Navigation Phase* (airport routing avoiding ORR).
  2. **Radha**: Hardcoded to an adjacent compound ($12.9312^\circ \text{N}, 77.6254^\circ \text{E}$). Used to show the *Emergency Phase* (photo upload SOS and community gather points).
  3. **Anonymous (New Resident)**: Generates a random UUID, saves it in `localStorage`, and requests live browser Geolocation coordinates.
* **Benefit**: Ensures the presentation runs exactly on script without typing credentials or waiting for SMS codes, while demonstrating isolated database session histories.

---

## 2. Weather Telemetry Override (Mock Sliders)
* **Constraint**: If the hackathon judging happens on a clear, sunny day in Bengaluru, live meteorological APIs would return $0\text{mm}$ precipitation, meaning the system would evaluate risk as "Low" and refuse to trigger alerts or detour routes.
* **Implementation**: The backend `get_weather_telemetry` tool accepts a `mock_precipitation` parameter. In the UI, a hidden **"Demo Admin Control Panel"** (or simple slider) allows the presenter to:
  * Force weather to **"Monsoon Peak"** ($45\text{mm/hr}$ rainfall).
  * Immediately triggers the ADK risk agents to recalculate the Flood Vulnerability Index (FVI), shifting Rajesh's status from "Safe" to "High Risk."
* **Benefit**: Guarantees that active flood triggers, dynamic checklist alerts, and alternative routing calculations can be demonstrated on-demand.

---

## 3. Pre-populated Bounding Box Flood Polygons
* **Constraint**: In a real disaster, flood boundaries (polygons) are slowly aggregated from hours of radar mapping and municipal reports. For a 5-minute live demo, we cannot wait for data to gather.
* **Implementation**: The BigQuery database is pre-seeded with two active "inundation polygons" representing flooded stretches of the Outer Ring Road (ORR) near Silk Board and Bellandur.
* **Benefit**: When Rajesh requests navigation to the airport, the backend immediately detects the Turf.js intersection with the pre-seeded Silk Board polygon, forcing the route generator to trigger waypoint-injected detours on the spot.

---

## 4. Parametric What-If Simulation (Hydrological Shortcut)
* **Constraint**: A true hydrological simulation models complex fluid dynamics, topography grids, soil permeability, and sewer flows, which requires supercomputer runtime.
* **Implementation**: The `run_what_if_simulation` tool uses a simplified **parametric impact formula** calculated via BigQuery SQL:
  * Each storm water drain has a pre-defined zone of influence (bounding box).
  * Clearing a drain or adding a water pump at coordinate $X, Y$ reduces the dynamic runoff score ($R$) inside that cell by a fixed coefficient (e.g., desilting drain = $-35\%$ risk; deploying pump = $-15\%$ risk).
  * The tool instantly yields a predicted FVI reduction and confidence score ($\approx 85-90\%$) in under $500\text{ms}$.
* **Benefit**: Shows officials immediate visual feedback on the map dashboard in real-time, demonstrating decision intelligence without compute latency.

---

## 5. Google Elevation API Fallbacks
* **Constraint**: Google Elevation API calls have strict rate limits and latency.
* **Implementation**: The backend cache maps 100+ key grid cells across Bengaluru (focused on HSR Layout, Koramangala, and Silk Board). If the Google Elevation API fails or times out, the `get_elevation_profile` tool falls back to this local cached topography table in BigQuery.
* **Benefit**: Provides zero-latency altitude lookup and ensures the app remains functional even if external API limits are exceeded during heavy evaluation traffic.

---

## 6. Single Global Official Session
* **Constraint**: Only one global instance of the RWA/City Official Command Center is simulated.
* **Implementation**: There is no login panel for officials. The dashboard listens to a unified server-sent event (SSE) stream (`/api/official/live-sos-feed`), updating the map markers immediately whenever *any* resident profile (Rajesh, Radha, or Anonymous) posts an update or uploads a photo.
