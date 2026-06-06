import math
import logging
import os
import asyncio
from typing import Any, Callable
from functools import cached_property

import vertexai
from dotenv import load_dotenv
from google.cloud import logging as google_cloud_logging

from google.adk.agents.llm_agent import Agent
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TransportProtocol
from vertexai.preview.reasoning_engines import A2aAgent
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.runners import Runner
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService

from .utils.telemetry import setup_telemetry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_prime(n: int) -> bool:
    """Check if a number is prime.

    Args:
        n: The integer to check.

    Returns:
        True if the number is prime, False otherwise.
    """
    logger.info(f"check_prime tool called with n={n}")
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.isqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True

def get_fibonacci(n: int) -> list[int]:
    """Generate a Fibonacci sequence up to length n.

    Args:
        n: The length of the sequence to generate.

    Returns:
        A list containing the Fibonacci sequence.
    """
    logger.info(f"get_fibonacci tool called with n={n}")
    if n <= 0:
        return []
    if n == 1:
        return [0]
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq[:n]

# Define the Math Agent
math_agent = Agent(
    model="gemini-3.5-flash",
    name="math_agent",
    instruction="""You are a math helper agent. You specialize in checking primality of numbers and generating Fibonacci sequences.
Always use your tools to perform these mathematical checks and sequences when requested by the user. Do not try to solve them yourself.""",
    tools=[check_prime, get_fibonacci],
)

# Build agent card
agent_card = AgentCard(
    name='math_agent',
    description='An ADK Agent',
    url='http://localhost:80/a2a',
    version='0.0.1',
    preferred_transport=TransportProtocol.http_json,
    capabilities=AgentCapabilities(),
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    supports_authenticated_extended_card=False,
    skills=[
        AgentSkill(
            id='math_agent',
            name='model',
            description='I am a math helper agent. I specialize in checking primality of numbers and generating Fibonacci sequences.\nAlways use my tools to perform these mathematical checks and sequences when requested by the user. Do not try to solve them yourself.',
            tags=['llm'],
            examples=[],
        ),
        AgentSkill(
            id='math_agent-check_prime',
            name='check_prime',
            description='Check if a number is prime.\n\nArgs:\n    n: The integer to check.\n\nReturns:\n    True if the number is prime, False otherwise.',
            tags=['llm', 'tools'],
        ),
        AgentSkill(
            id='math_agent-get_fibonacci',
            name='get_fibonacci',
            description='Generate a Fibonacci sequence up to length n.\n\nArgs:\n    n: The length of the sequence to generate.\n\nReturns:\n    A list containing the Fibonacci sequence.',
            tags=['llm', 'tools'],
        ),
    ],
)

def create_runner() -> Runner:
    logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
    artifact_service = (
        GcsArtifactService(bucket_name=logs_bucket_name)
        if logs_bucket_name
        else InMemoryArtifactService()
    )
    return Runner(
        app_name="math_agent",
        agent=math_agent,
        artifact_service=artifact_service,
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
        credential_service=InMemoryCredentialService(),
    )

def create_agent_executor(**kwargs) -> A2aAgentExecutor:
    runner = create_runner()
    return A2aAgentExecutor(runner=runner)

class AgentEngineApp(A2aAgent):
    def set_up(self) -> None:
        vertexai.init()
        setup_telemetry()
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)

# Expose as root_agent (this matches ADK default)
root_agent = AgentEngineApp(
    agent_card=agent_card,
    agent_executor_builder=create_agent_executor,
)
