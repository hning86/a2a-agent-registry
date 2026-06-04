import math
import logging
from google.adk.agents.llm_agent import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

from functools import cached_property
from google.adk.models import Gemini
from google.genai import Client

# Subclass Gemini to force the API client to use the "global" location on Vertex AI.
# This avoids 404 errors when resolving models like gemini-3.5-flash which are not in us-central1.
class GlobalGemini(Gemini):
    @cached_property
    def api_client(self) -> Client:
        # If running in Vertex AI, use global location.
        # Otherwise, fall back to standard Gemini API client.
        if self.model.startswith('projects/'):
            return Client(vertexai=True, location="global")
        # Even for developer API name like gemini-3.5-flash, the Reasoning Engine runtime
        # defaults to Vertex AI. So we should force vertexai=True with location="global".
        return Client(vertexai=True, location="global")

# Define the Math Agent
math_agent = Agent(
    model=GlobalGemini(model="gemini-3.5-flash"),
    name="math_agent",
    instruction="""You are a math helper agent. You specialize in checking primality of numbers and generating Fibonacci sequences.
Always use your tools to perform these mathematical checks and sequences when requested by the user. Do not try to solve them yourself.""",
    tools=[check_prime, get_fibonacci],
)
