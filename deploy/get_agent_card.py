import sys
import json
import logging
from google.adk.integrations.agent_registry import AgentRegistry

# Suppress verbose warnings/logs
logging.getLogger("google_adk").setLevel(logging.WARNING)

def main():
    project_id = "ninghai-ccai"
    location = "us-central1"
    agent_display_name = "math_agent"

    print(f"Connecting to Agent Registry in project: {project_id}, location: {location}...")
    registry = AgentRegistry(project_id=project_id, location=location)

    print(f"Listing agents to locate '{agent_display_name}'...")
    agents = registry.list_agents(page_size=100).get("agents", [])
    
    target_agent = None
    for a in agents:
        if a.get("displayName") == agent_display_name:
            target_agent = a
            break

    if not target_agent:
        print(f"Error: Agent '{agent_display_name}' not found in the registry.", file=sys.stderr)
        sys.exit(1)

    print(f"Retrieving details for registry agent: {target_agent.get('name')}...")
    info = registry.get_agent_info(target_agent.get("name"))
    
    card = info.get("card")
    if not card:
        print(f"Error: No agent card metadata associated with agent '{agent_display_name}'.", file=sys.stderr)
        sys.exit(1)

    print("\n--- AGENT CARD ---")
    print(json.dumps(card, indent=2))

if __name__ == "__main__":
    main()
