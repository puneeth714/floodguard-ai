import os
from google.adk.tools.tool_context import ToolContext
from app.db.bigquery_client import BigQueryClientWrapper

def get_operational_status(tool_context: ToolContext) -> dict:
    """
    Queries current operational metrics from the municipal database.
    This includes:
    - Active resident SOS distress counts, locations, and special needs.
    - Blocked and cleared stormwater drain lists.
    - Status of tactical suction pumps.
    """
    bq_client = BigQueryClientWrapper()
    
    # 1. Fetch latest state of all SOS alerts (using deduplication window function to avoid streaming buffer duplicates)
    sos_query = f"""
    SELECT session_id, user_id, lat, lng, detected_depth, photo_url, status, timestamp
    FROM (
        SELECT *, ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY timestamp DESC) as rn
        FROM `{bq_client.dataset_ref}.active_sos`
    )
    WHERE rn = 1 AND status != 'resolved'
    """
    try:
        sos_records = bq_client.execute_query(sos_query)
    except Exception as e:
        print(f"Error querying active_sos: {e}")
        sos_records = []
        
    # 2. Fetch drains status
    drain_query = f"""
    SELECT drain_id, name, lat, lng, status
    FROM `{bq_client.dataset_ref}.drainage_network`
    """
    try:
        drains = bq_client.execute_query(drain_query)
    except Exception as e:
        print(f"Error querying drainage_network: {e}")
        drains = []
        
    # 3. Compile static/dynamic water pump list (placed in HSR Layout basin)
    pumps = [
        {"pump_id": "PUMP_HSR_4_01", "name": "Sector 4 High Capacity Suction", "lat": 12.9279, "lng": 77.6271, "status": "active", "flow_rate_lps": 120.0},
        {"pump_id": "PUMP_HSR_4_02", "name": "Sector 4 Outer Ring Aux", "lat": 12.9290, "lng": 77.6285, "status": "stopped", "flow_rate_lps": 80.0},
        {"pump_id": "PUMP_HSR_2_01", "name": "Sector 2 Flyover Drainage Unit", "lat": 12.9340, "lng": 77.6320, "status": "active", "flow_rate_lps": 150.0}
    ]
    
    # Decode Custom Stranded Details encoded inside user_id string: "resident:people_count=X:needs=Y"
    parsed_sos = []
    for s in sos_records:
        user_id_str = s.get("user_id", "resident")
        people_count = 1
        needs = "None"
        
        if ":" in user_id_str:
            parts = user_id_str.split(":")
            for p in parts:
                if p.startswith("people_count="):
                    try:
                        people_count = int(p.split("=")[1])
                    except Exception:
                        pass
                elif p.startswith("needs="):
                    needs = p.split("=")[1]
                    
        parsed_sos.append({
            "session_id": s["session_id"],
            "lat": s["lat"],
            "lng": s["lng"],
            "detected_depth_cm": s.get("detected_depth"),
            "status": s["status"],
            "stranded_people_count": people_count,
            "special_needs": needs
        })
        
    return {
        "active_distress_alerts": parsed_sos,
        "stormwater_drains": drains,
        "water_pumps": pumps
    }
