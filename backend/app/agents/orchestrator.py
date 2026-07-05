import os
import asyncio
from typing import Optional
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from app.agents.graph import orchestrator_agent
from app.core.config import settings
from app.core.profiles import TEST_PROFILES

# Initialize a global session service to persist sessions across runs/requests
_global_session_service = InMemorySessionService()

class Orchestrator:
    """
    Orchestrates specialized sub-agents dynamically using Google ADK 2.0 LlmAgents.
    """
    def __init__(self):
        self.session_service = _global_session_service
        self.runner = Runner(
            agent=orchestrator_agent,
            app_name="floodguard",
            session_service=self.session_service
        )

    async def run(
        self, 
        session_id: str, 
        user_query: str, 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None, 
        destination: Optional[str] = None, 
        image_path: Optional[str] = None,
        user_role: str = "resident",
        demo_profile: Optional[str] = None
    ) -> dict:
        """
        Executes the Orchestrator LLM agent and yields the final response along with
        the populated session state.
        """
        # Resolve active demo profile if in test mode or specified
        active_profile = demo_profile
        if not active_profile and settings.ENVIRONMENT_MODE == "test":
            active_profile = settings.DEFAULT_DEMO_PROFILE

        elevation_altitude = None
        precipitation_mm_hr = None
        use_mock = False

        if active_profile and active_profile in TEST_PROFILES:
            profile = TEST_PROFILES[active_profile]
            latitude = latitude or profile["latitude"]
            longitude = longitude or profile["longitude"]
            destination = destination or profile["destination"]
            user_role = user_role or profile["role"]
            elevation_altitude = profile["elevation_altitude"]
            precipitation_mm_hr = profile["precipitation_mm_hr"]
            use_mock = profile["use_mock"]

        # 1. Prepare initial session state
        state_data = {
            "session_id": session_id,
            "user_query": user_query,
            "latitude": latitude,
            "longitude": longitude,
            "destination": destination,
            "image_path": image_path,
            "image_uploaded": image_path is not None and image_path != "",
            "user_role": user_role,
            "elevation_altitude": elevation_altitude,
            "precipitation_mm_hr": precipitation_mm_hr,
            "use_mock": use_mock,
            "demo_profile": active_profile
        }
        
        # 2. Initialize or fetch existing session
        try:
            session = await self.session_service.get_session(
                app_name="floodguard",
                user_id="user",
                session_id=session_id
            )
        except Exception:
            session = None
            
        if not session:
            await self.session_service.create_session(
                app_name="floodguard",
                user_id="user",
                session_id=session_id,
                state=state_data
            )
        else:
            # Update state variables in existing session
            for k, v in state_data.items():
                if v is not None:
                    session.state[k] = v

        # 3. Create content request payload
        content = types.Content(role='user', parts=[types.Part(text=user_query)])


        # 4. Stream runner events to get final answer
        final_text = ""
        async for event in self.runner.run_async(user_id="user", session_id=session_id, new_message=content):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_text = event.content.parts[0].text

                
        # 5. Fetch completed session state to return to API layer
        updated_session = await self.session_service.get_session(
            app_name="floodguard",
            user_id="user",
            session_id=session_id
        )
        
        return {
            "final_response": final_text,
            "state": updated_session.state if updated_session else {}
        }

if __name__ == "__main__":
    # Small test loop to verify ADK execution
    async def main():
        orchestrator = Orchestrator()
        result = await orchestrator.run(
            session_id="test_session_123",
            user_query="I am at Sector 4 and it's raining heavily. FVI details?",
            latitude=12.9279,
            longitude=77.6271
        )
        print("Final Response:")
        print(result["final_response"])
        print("Session State:")
        print(result["state"])

    asyncio.run(main())