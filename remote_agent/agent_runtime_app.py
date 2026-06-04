# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

import google.protobuf.json_format as json_format
from pydantic import BaseModel

# Monkey patch json_format.MessageToJson to support Pydantic models (fixes vertexai SDK bug)
original_message_to_json = json_format.MessageToJson

def custom_message_to_json(message, *args, **kwargs):
    if isinstance(message, BaseModel):
        return message.model_dump_json()
    return original_message_to_json(message, *args, **kwargs)

json_format.MessageToJson = custom_message_to_json

import logging
import os
import asyncio
from typing import Any, Callable


import vertexai
from dotenv import load_dotenv
from google.cloud import logging as google_cloud_logging

from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TransportProtocol
from vertexai.preview.reasoning_engines import A2aAgent
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.runners import Runner
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService

from remote_agent.agent import math_agent
from remote_agent.utils.telemetry import setup_telemetry


# Load environment variables from .env file at runtime
load_dotenv()


# Build agent card synchronously for reasoning engine initialization
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
    """Create a runner instance with Cloud Storage or In-Memory artifact service."""
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
    """Create the agent executor."""
    runner = create_runner()
    return A2aAgentExecutor(runner=runner)


class AgentEngineApp(A2aAgent):
    def set_up(self) -> None:
        """Initialize logging and telemetry."""
        vertexai.init()
        setup_telemetry()
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)


agent_runtime = AgentEngineApp(
    agent_card=agent_card,
    agent_executor_builder=create_agent_executor,
)
