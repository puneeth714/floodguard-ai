# agent.py inside the single agent directory to make it compatible with ADK CLI
import sys
import os

# Add backend directory to Python path if running CLI externally
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Expose orchestrator_agent as the default agent for adk command
from app.agents.graph import orchestrator_agent as root_agent
