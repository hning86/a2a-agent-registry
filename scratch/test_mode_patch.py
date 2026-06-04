import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from app.consumer_agent import get_math_agent_client

# Define class property for mode
print("Applying class-level property patch...")
RemoteA2aAgent.mode = property(lambda self: None)

try:
    client = get_math_agent_client()
    print("Fetched client successfully.")
    
    # Try reading mode
    val = client.mode
    print(f"Successfully read client.mode: {val}")
    
    # Try check
    check = client.mode not in ('single_turn', 'task')
    print(f"Mode check result: {check}")
except Exception as e:
    print(f"Failed: {type(e).__name__}: {e}")
