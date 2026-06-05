import json
import os
import subprocess
import re
from datetime import datetime, timezone

PROJECT_ID = "ninghai-ccai"
REGION = "us-central1"
DISPLAY_NAME = "math_agent"
METADATA_FILE = "deploy/deployment_metadata.json"
REQUIREMENTS_FILE = "remote_agent/requirements.txt"

def main():
    agent_engine_id = None
    
    # 1. Read existing metadata if it exists to perform an update
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                metadata = json.load(f)
                runtime_id = metadata.get("remote_agent_runtime_id")
                if runtime_id:
                    match = re.search(r"reasoningEngines/(\d+)", runtime_id)
                    if match:
                        agent_engine_id = match.group(1)
                        print(f"Found existing Agent Engine ID: {agent_engine_id}")
        except Exception as e:
            print(f"Warning: Could not read {METADATA_FILE}: {e}")

    # 2. Build deployment command using ADK
    cmd = [
        "uv", "run", "adk", "deploy", "agent_engine",
        "--project", PROJECT_ID,
        "--region", REGION,
        "--display_name", DISPLAY_NAME,
        "--requirements_file", REQUIREMENTS_FILE,
    ]
    
    if agent_engine_id:
        cmd.extend(["--agent_engine_id", agent_engine_id])
        
    cmd.append("remote_agent")
    
    print(f"Running command: {' '.join(cmd)}")
    
    # 3. Execute deployment
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print output to stdout/stderr
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
        
    if result.returncode != 0:
        print("Deployment failed!")
        exit(result.returncode)
        
    # 4. Parse the new/updated resource name from stdout
    new_runtime_id = None
    # Look for patterns like projects/.../locations/.../reasoningEngines/...
    match = re.search(r"(projects/\S+/locations/\S+/reasoningEngines/\d+)", result.stdout + "\n" + result.stderr)
    if match:
        new_runtime_id = match.group(1)
                
    if not new_runtime_id and agent_engine_id:
        new_runtime_id = f"projects/{PROJECT_ID}/locations/{REGION}/reasoningEngines/{agent_engine_id}"
        
    if new_runtime_id:
        print(f"Deployment succeeded. Registered resource name: {new_runtime_id}")
        # 5. Write updated metadata file
        new_metadata = {
            "remote_agent_runtime_id": new_runtime_id,
            "deployment_target": "agent_runtime",
            "is_a2a": True,
            "deployment_timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(METADATA_FILE, "w") as f:
            json.dump(new_metadata, f, indent=2)
            f.write("\n")
        print(f"Updated {METADATA_FILE} successfully.")
    else:
        print("Warning: Could not parse deployed resource ID from output.")

if __name__ == "__main__":
    main()
