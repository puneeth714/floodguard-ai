"""
orchestrator.py

FloodGuard AI

The Orchestrator is responsible for coordinating
specialized AI agents.

It receives a ConversationState,
decides which agents are required,
executes them,
and returns the updated state.
"""

from __future__ import annotations

import logging

from backend.app.agents.state import ConversationState
from backend.app.agents.vision_agent import VisionAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Coordinates all AI agents.

    The orchestrator never performs business logic itself.
    It only decides which agents to invoke.
    """

    def __init__(self):

        # Register all available agents

        self.vision_agent = VisionAgent()

        # Future

        # self.weather_agent = WeatherAgent()

        # self.routing_agent = RoutingAgent()

        # self.policy_agent = PolicyAgent()

    def run(self, state: ConversationState) -> ConversationState:
        """
        Execute all required agents.

        Parameters
        ----------
        state : ConversationState

        Returns
        -------
        ConversationState
        """

        logger.info("Starting Orchestrator...")

        # ----------------------------------------------------
        # Vision Agent
        # ----------------------------------------------------

        if self.vision_agent.can_execute(state):

            logger.info("Executing VisionAgent")

            state = self.vision_agent.execute(state)

        # ----------------------------------------------------
        # Future Agents
        # ----------------------------------------------------

        #
        # if self.weather_agent.can_execute(state):
        #     state = self.weather_agent.execute(state)
        #
        # if self.routing_agent.can_execute(state):
        #     state = self.routing_agent.execute(state)
        #
        # if self.policy_agent.can_execute(state):
        #     state = self.policy_agent.execute(state)

        logger.info("Orchestration Completed.")

        return state


if __name__ == "__main__":

    state = ConversationState(
        session_id="demo-session",
        image_uploaded=True,
        image_path="backend/app/tools/sample_image.png",
    )

    orchestrator = Orchestrator()

    result = orchestrator.run(state)

    print(result.model_dump_json(indent=4))