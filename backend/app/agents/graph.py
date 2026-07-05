from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from app.core.config import settings

# Import original single tools directly
from app.tools.vision import VisionTool
from app.tools.weather import get_weather_telemetry
from app.tools.elevation import get_elevation_profile
from app.tools.routing import calculate_safe_route
from app.tools.places import geocode_place
from app.tools.simulation import run_what_if_simulation
from app.tools.guidelines import search_disaster_guidelines
from app.tools.fvi import calculate_flood_vulnerability_index
from app.tools.operational import get_operational_status

# Import prompts
from app.agents.prompts import (
    ORCHESTRATOR_INSTRUCTION,
    VISION_AGENT_INSTRUCTION,
    GEOSPATIAL_AGENT_INSTRUCTION,
    POLICY_AGENT_INSTRUCTION
)


# Session context helper tool
def get_session_context(tool_context: ToolContext) -> dict:
    """
    Retrieves the current session context metadata (user role, coordinates, destination, and uploaded image path).
    """
    from app.core.profiles import TEST_PROFILES

    lat = tool_context.state.get("latitude")
    lng = tool_context.state.get("longitude")
    dest = tool_context.state.get("destination")
    role = tool_context.state.get("user_role")
    img = tool_context.state.get("image_path")
    profile_name = tool_context.state.get("demo_profile")
    lang = tool_context.state.get("language") or "en"

    # If running in test mode and coordinates are empty (e.g. initial adk web turn),
    # auto-load the default mock profile details.
    if (lat is None or lng is None) and settings.ENVIRONMENT_MODE == "test":
        active_profile = profile_name or settings.DEFAULT_DEMO_PROFILE
        if active_profile in TEST_PROFILES:
            profile = TEST_PROFILES[active_profile]
            lat = lat or profile["latitude"]
            lng = lng or profile["longitude"]
            dest = dest or profile["destination"]
            role = role or profile["role"]
            
            # Inject into state so it's persisted for other tools to read
            tool_context.state["latitude"] = lat
            tool_context.state["longitude"] = lng
            tool_context.state["destination"] = dest
            tool_context.state["user_role"] = role
            tool_context.state["elevation_altitude"] = profile["elevation_altitude"]
            tool_context.state["precipitation_mm_hr"] = profile["precipitation_mm_hr"]
            tool_context.state["use_mock"] = profile["use_mock"]
            tool_context.state["demo_profile"] = active_profile

    return {
        "user_role": role or "resident",
        "latitude": lat,
        "longitude": lng,
        "destination": dest,
        "image_path": img,
        "language": lang
    }


# Vision Agent (LlmAgent)
vision_agent = LlmAgent(
    model=settings.GEMINI_MODEL,
    name="VisionAgent",
    description="Analyzes uploaded flood photos to estimate severity, depth, and road blockages.",
    instruction=VISION_AGENT_INSTRUCTION,
    tools=[get_session_context, VisionTool().analyze_flood_image]
)

# Geospatial Agent (LlmAgent)
geospatial_agent = LlmAgent(
    model=settings.GEMINI_MODEL,
    name="GeospatialAgent",
    description="Resolves locations, weather & elevation telemetry, route blockages, and calculates FVI.",
    instruction=GEOSPATIAL_AGENT_INSTRUCTION,
    tools=[
        get_session_context,
        geocode_place,
        get_weather_telemetry,
        get_elevation_profile,
        calculate_safe_route,
        calculate_flood_vulnerability_index,
        get_operational_status
    ]
)

# Policy Agent (LlmAgent)
policy_agent = LlmAgent(
    model=settings.GEMINI_MODEL,
    name="PolicyAgent",
    description="Queries disaster response guidelines (RAG) and runs what-if hydrological simulations.",
    instruction=POLICY_AGENT_INSTRUCTION,
    tools=[get_session_context, run_what_if_simulation, search_disaster_guidelines, get_operational_status]
)

# Orchestrator Agent (LlmAgent)
orchestrator_agent = LlmAgent(
    model=settings.GEMINI_MODEL,
    name="Orchestrator",
    description="Coordinates all flood resilience tasks and specialized sub-agents.",
    instruction=ORCHESTRATOR_INSTRUCTION,
    tools=[get_session_context],
    sub_agents=[vision_agent, geospatial_agent, policy_agent]
)


