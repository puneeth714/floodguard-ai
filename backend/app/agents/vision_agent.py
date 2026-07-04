"""
vision_agent.py

FloodGuard AI
Vision Agent

Purpose
-------
The Vision Agent is responsible for invoking the Vision Tool whenever
an uploaded image is available.

It does NOT perform image analysis itself.

Responsibilities:
- Receive ConversationState
- Validate whether an image exists
- Call VisionTool
- Store VisionResult in ConversationState
- Update execution metadata
- Return updated ConversationState
"""

from __future__ import annotations

import logging

from backend.app.agents.state import ConversationState
from backend.app.tools.vision import VisionTool

logger = logging.getLogger(__name__)


class VisionAgent:
    """
    AI Agent responsible for flood image analysis.

    This agent wraps the VisionTool and updates the shared
    ConversationState.
    """

    AGENT_NAME = "VisionAgent"

    def __init__(self):
        self.vision_tool = VisionTool()

    def can_execute(self, state: ConversationState) -> bool:
        """
        Returns True if an image has been uploaded.
        """

        return (
            state.image_uploaded
            and state.image_path is not None
            and state.image_path != ""
        )

    def execute(self, state: ConversationState) -> ConversationState:
        """
        Execute flood image analysis.

        Parameters
        ----------
        state : ConversationState

        Returns
        -------
        ConversationState
        """

        logger.info("Starting VisionAgent...")

        if not self.can_execute(state):
            logger.info("No uploaded image found.")

            state.errors.append(
                "VisionAgent skipped because no image was provided."
            )

            return state

        try:

            vision_result = self.vision_tool.analyze_flood_image(
                state.image_path
            )

            state.vision_result = vision_result

            # Optional summary values
            #state.flood_severity = vision_result.severity.value

            state.completed_agents.append(self.AGENT_NAME)

            logger.info("VisionAgent completed successfully.")

        except Exception as e:

            logger.exception("VisionAgent failed.")

            state.errors.append(str(e))

        return state


if __name__ == "__main__":

    state = ConversationState(
        session_id="demo-session",
        image_uploaded=True,
        image_path="backend/app/tools/sample_image.png",
    )

    agent = VisionAgent()

    updated_state = agent.execute(state)

    print(updated_state.model_dump_json(indent=4))