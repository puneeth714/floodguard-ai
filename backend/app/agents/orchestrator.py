import os
import asyncio
from typing import Optional, AsyncGenerator
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from app.agents.graph import orchestrator_agent
from app.core.config import settings
from app.core.profiles import TEST_PROFILES

# Initialize a global session service to persist sessions across runs/requests
_global_session_service = InMemorySessionService()

class ModelManager:
    """
    Manages the available models and tracks the active model.
    Enables round-robin model failover on 429 or other API exceptions.
    Prioritizes testing gemma-4-31b-it by placing it first.
    """
    MODELS = [
        "gemma-4-31b-it",
        "gemma-4-26b-a4b-it",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview"
    ]
    current_index = 0

    @classmethod
    def get_current_model(cls) -> str:
        return cls.MODELS[cls.current_index]

    @classmethod
    def switch_to_next_model(cls) -> str:
        cls.current_index = (cls.current_index + 1) % len(cls.MODELS)
        return cls.get_current_model()

def set_agent_model_recursive(agent, model_name: str):
    """
    Recursively updates the model configuration name on an ADK agent and all of its sub-agents.
    """
    agent.model = model_name
    if hasattr(agent, "sub_agents") and agent.sub_agents:
        for sub in agent.sub_agents:
            set_agent_model_recursive(sub, model_name)

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

    def _prepare_session_state(
        self,
        session_id: str,
        user_query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        destination: Optional[str] = None,
        image_path: Optional[str] = None,
        user_role: str = "resident",
        demo_profile: Optional[str] = None,
        language: Optional[str] = "en"
    ) -> dict:
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

        return {
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
            "demo_profile": active_profile,
            "language": language
        }

    async def run(
        self, 
        session_id: str, 
        user_query: str, 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None, 
        destination: Optional[str] = None, 
        image_path: Optional[str] = None,
        user_role: str = "resident",
        demo_profile: Optional[str] = None,
        language: Optional[str] = "en"
    ) -> dict:
        """
        Executes the Orchestrator LLM agent and yields the final response along with
        the populated session state.
        Supports model failover retries.
        """
        state_data = self._prepare_session_state(
            session_id, user_query, latitude, longitude, destination, image_path, user_role, demo_profile, language
        )
        
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
            for k, v in state_data.items():
                if v is not None:
                    session.state[k] = v

        content = types.Content(role='user', parts=[types.Part(text=user_query)])

        max_retries = len(ModelManager.MODELS)
        last_exception = None

        for attempt in range(max_retries):
            current_model = ModelManager.get_current_model()
            set_agent_model_recursive(orchestrator_agent, current_model)
            print(f"Orchestrator Run: Attempt {attempt + 1}/{max_retries} using model {current_model}")
            
            try:
                final_text = ""
                async for event in self.runner.run_async(user_id="user", session_id=session_id, new_message=content):
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            final_text = event.content.parts[0].text

                updated_session = await self.session_service.get_session(
                    app_name="floodguard",
                    user_id="user",
                    session_id=session_id
                )
                
                return {
                    "final_response": final_text,
                    "state": updated_session.state if updated_session else {}
                }
            except Exception as e:
                last_exception = e
                print(f"Error with model {current_model}: {e}")
                next_model = ModelManager.switch_to_next_model()
                print(f"Switched model pointer to fallback: {next_model}")
                await asyncio.sleep(1)

        raise last_exception

    async def run_stream(
        self,
        session_id: str,
        user_query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        destination: Optional[str] = None,
        image_path: Optional[str] = None,
        user_role: str = "resident",
        demo_profile: Optional[str] = None,
        language: Optional[str] = "en"
    ) -> AsyncGenerator[dict, None]:
        """
        Runs the Orchestrator loop yielding intermediate agent node changes and tool calls
        to avoid leaving the user without progress updates.
        Supports model failover retries.
        """
        state_data = self._prepare_session_state(
            session_id, user_query, latitude, longitude, destination, image_path, user_role, demo_profile, language
        )
        
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
            for k, v in state_data.items():
                if v is not None:
                    session.state[k] = v

        content = types.Content(role='user', parts=[types.Part(text=user_query)])
        
        max_retries = len(ModelManager.MODELS)
        last_exception = None

        for attempt in range(max_retries):
            current_model = ModelManager.get_current_model()
            set_agent_model_recursive(orchestrator_agent, current_model)
            yield {"type": "status", "content": f"Using model: {current_model}..."}
            
            try:
                final_text = ""
                async for event in self.runner.run_async(user_id="user", session_id=session_id, new_message=content):
                    # Check for active tool calls
                    func_calls = event.get_function_calls()
                    if func_calls:
                        names = [call.name for call in func_calls]
                        yield {"type": "tool", "content": f"Invoking tools: {', '.join(names)}"}
                    elif event.is_final_response():
                        if event.content and event.content.parts:
                            final_text = event.content.parts[0].text
                    else:
                        node_name = event.node_name
                        if node_name:
                            yield {"type": "status", "content": f"Running {node_name}..."}

                # Fetch final state to complete
                updated_session = await self.session_service.get_session(
                    app_name="floodguard",
                    user_id="user",
                    session_id=session_id
                )
                
                yield {
                    "type": "final",
                    "content": final_text,
                    "state": updated_session.state if updated_session else {}
                }
                return # Successful execution finished!
            except Exception as e:
                last_exception = e
                print(f"Stream error with model {current_model}: {e}")
                yield {"type": "status", "content": f"Model {current_model} failed. Trying fallback..."}
                next_model = ModelManager.switch_to_next_model()
                await asyncio.sleep(1)

        raise last_exception