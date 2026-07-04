import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from app.db.bigquery_client import BigQueryClientWrapper

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

def run_what_if_simulation(
    intervention_type: str, 
    details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Simulates municipal flood mitigation interventions (e.g., desilting stormwater drains 
    or deploying mobile pumps) and calculates the dynamic risk reduction across grid cells.
    
    Args:
        intervention_type: Type of action ('desilt_drain' or 'deploy_pump').
        details: Dict containing parameters:
                 - For 'desilt_drain': 'drain_id' (str)
                 - For 'deploy_pump': 'lat' (float), 'lng' (float), 'capacity_gpm' (int)
                 
    Returns:
        Dict containing baseline vs simulated FVI scores, reduction percentage, 
        estimated residents protected, and an engineering explanation.
    """
    bq_wrapper = BigQueryClientWrapper()
    dataset = bq_wrapper.dataset_ref
    
    # 1. Fetch baseline vulnerability grids and drainage locations from BigQuery
    try:
        # Standard monoon rain load parameter (e.g., heavy precipitation = 35 mm/hr)
        rain_load = 35.0
        
        # Pull grid cells
        grids_query = f"SELECT lat, lng, altitude, slope, drainage_capacity FROM `{dataset}.vulnerability_grids`"
        grids = bq_wrapper.execute_query(grids_query)
        
        if not grids:
            raise Exception("No vulnerability grids found in database.")
            
        # 2. Process Intervention Impact
        affected_count = 0
        baseline_fvi_sum = 0.0
        simulated_fvi_sum = 0.0
        
        # AHP Weights for FVI formula:
        # V = (w_elev * (864 - altitude)) + (w_slope * (3 - slope)) + (w_rain * rain) + (w_drain * (100 - drainage_capacity))
        w_elev = 0.35
        w_slope = 0.15
        w_rain = 0.30
        w_drain = 0.20
        
        for grid in grids:
            lat = grid["lat"]
            lng = grid["lng"]
            alt = grid["altitude"]
            slope = grid["slope"]
            base_capacity = grid["drainage_capacity"]
            
            # Calculate baseline FVI
            # Relative sink depth = 864 - altitude (capped at 0 if higher than surrounding)
            sink_depth = max(0.0, 864.0 - alt)
            flatness_penalty = max(0.0, 3.0 - slope)
            drain_penalty = max(0.0, 100.0 - base_capacity)
            
            base_fvi = (w_elev * sink_depth) + (w_slope * flatness_penalty) + (w_rain * rain_load) + (w_drain * drain_penalty)
            baseline_fvi_sum += base_fvi
            
            # Calculate simulated drainage capacity
            sim_capacity = base_capacity
            
            if intervention_type == "desilt_drain":
                # Find drain coordinates from database
                drain_id = details.get("drain_id")
                drain_query = f"SELECT lat, lng FROM `{dataset}.drainage_network` WHERE drain_id = '{drain_id}'"
                drain_rows = bq_wrapper.execute_query(drain_query)
                
                if drain_rows:
                    drain_lat = drain_rows[0]["lat"]
                    drain_lng = drain_rows[0]["lng"]
                    # Distance check (within approx 200m)
                    dist = ((lat - drain_lat)**2 + (lng - drain_lng)**2)**0.5
                    if dist < 0.002: # Proximity boundary
                        # Increase local drainage capacity by +30%
                        sim_capacity = min(100.0, base_capacity * 1.30)
                        affected_count += 1
                        
            elif intervention_type == "deploy_pump":
                pump_lat = float(details.get("lat", 0.0))
                pump_lng = float(details.get("lng", 0.0))
                # Distance check (within approx 150m)
                dist = ((lat - pump_lat)**2 + (lng - pump_lng)**2)**0.5
                if dist < 0.0015:
                    # Increase local drainage capacity by +45% (mobile pump)
                    sim_capacity = min(100.0, base_capacity * 1.45)
                    affected_count += 1
            
            # Calculate simulated FVI
            sim_drain_penalty = max(0.0, 100.0 - sim_capacity)
            sim_fvi = (w_elev * sink_depth) + (w_slope * flatness_penalty) + (w_rain * rain_load) + (w_drain * sim_drain_penalty)
            simulated_fvi_sum += sim_fvi
            
        # 3. Compile report metrics
        num_grids = len(grids)
        avg_base_fvi = baseline_fvi_sum / num_grids
        avg_sim_fvi = simulated_fvi_sum / num_grids
        fvi_reduction = ((avg_base_fvi - avg_sim_fvi) / avg_base_fvi) * 100 if avg_base_fvi > 0 else 0.0
        
        # Estimate protected residents (assume ~200 residents per affected grid point)
        protected_residents = affected_count * 200
        
        explanation = ""
        if intervention_type == "desilt_drain":
            explanation = (
                f"Desilting stormwater drain {details.get('drain_id')} clears blockages, "
                f"increasing local drainage throughput and reducing water accumulation risk. "
                f"Impacted {affected_count} surrounding grid points, lowering the local vulnerability score."
            )
        elif intervention_type == "deploy_pump":
            explanation = (
                f"Deploying a mobile water pump at coordinates ({details.get('lat')}, {details.get('lng')}) "
                f"actively evacuates standing water from the topographical sink. "
                f"Lowered risk levels for {affected_count} immediate residential properties."
            )
            
        return {
            "status": "success",
            "intervention": intervention_type,
            "affected_grid_points": affected_count,
            "baseline_avg_fvi": round(avg_base_fvi, 2),
            "simulated_avg_fvi": round(avg_sim_fvi, 2),
            "fvi_reduction_percent": round(fvi_reduction, 1),
            "estimated_residents_protected": protected_residents,
            "explanation": explanation,
            "confidence_score": 88 if affected_count > 0 else 50
        }
        
    except Exception as e:
        print(f"Hydrological simulation error (falling back to mock): {e}")
        # Fallback Mock report
        return {
            "status": "fallback_mock",
            "intervention": intervention_type,
            "affected_grid_points": 8,
            "baseline_avg_fvi": 65.4,
            "simulated_avg_fvi": 42.1,
            "fvi_reduction_percent": 35.6,
            "estimated_residents_protected": 1600,
            "explanation": "Fallback Simulation: Action reduces local water levels by approximately 35.6%.",
            "confidence_score": 85
        }
