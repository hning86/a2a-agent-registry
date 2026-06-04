import random
import logging
import httpx
from google.adk.agents.llm_agent import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.cli.utils.gcp_utils import get_access_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Define Local Tool
def roll_die(sides: int) -> int:
    """Roll a die with the specified number of sides and return the result.

    Args:
        sides: The number of sides the die has (e.g., 6, 8, 10, 20).

    Returns:
        An integer representing the rolled result.
    """
    logger.info(f"roll_die tool called with sides={sides}")
    return random.randint(1, sides)

# 2. Define Local Roll Agent
roll_agent = Agent(
    model="gemini-3.5-flash",
    name="roll_agent",
    instruction="""You are a specialized dice roller agent.
Always use the roll_die tool to roll dice. Do not make up results.
Report the final rolled result clearly to the user.""",
    tools=[roll_die],
)

# Create an authenticated HTTP client for A2A communication with GCP
def create_authenticated_client() -> httpx.AsyncClient:
    token = get_access_token()
    return httpx.AsyncClient(
        headers={"Authorization": f"Bearer {token}"},
        timeout=httpx.Timeout(timeout=600.0)
    )

from google.adk.integrations.agent_registry import AgentRegistry

# Initialize registry client
registry = AgentRegistry(project_id="ninghai-ccai", location="us-central1")

# Retrieve math_agent dynamically from GCP Agent Registry
def get_math_agent_client() -> RemoteA2aAgent:
    agents = registry.list_agents(page_size=100).get("agents", [])
    for a in agents:
        if a.get("displayName") == "math_agent":
            return registry.get_remote_a2a_agent(
                a.get("name"),
                httpx_client=create_authenticated_client(),
            )
    raise RuntimeError("math_agent not found in GCP Agent Registry")

math_agent_client = get_math_agent_client()


# 4. Define Root Orchestrator Agent
orchestrator_agent = Agent(
    model="gemini-3.5-flash",
    name="orchestrator_agent",
    global_instruction="You are MathDiceBot, an advanced multi-agent assistant.",
    instruction="""You are the main orchestrator agent. You have access to:
1. `roll_agent` (local sub-agent) for rolling dice.
2. `math_agent` (remote A2A sub-agent) for prime number checking and generating Fibonacci sequences.

CRITICAL: You are NOT allowed to perform mathematical calculations, check primality of numbers, or generate sequences yourself. You MUST delegate all prime checks and Fibonacci sequences to `math_agent`.
Delegate work as follows:
- For rolling dice, use `roll_agent`.
- For checking if a number is prime or finding Fibonacci sequences, use `math_agent`.
- When asked to "roll a die and check if the result is prime", first call the `roll_agent` to get a roll, then pass that rolled number to the `math_agent` to check if it's prime.
Present all results beautifully and clearly to the user. Explain which agent performed which action.""",
    sub_agents=[roll_agent, math_agent_client],
)
