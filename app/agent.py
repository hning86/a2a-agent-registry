# This file acts as the main entry point for the ADK CLI tools (adk run, adk web).
# It exposes our orchestrator_agent as the required 'root_agent' variable.

from app.consumer_agent import orchestrator_agent as root_agent

__all__ = ["root_agent"]
