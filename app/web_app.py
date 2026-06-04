import os
import uuid
import logging
from dotenv import load_dotenv
load_dotenv()
import asyncio
import json
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.genai import types as genai_types
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from app.agent import root_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="A2A Demo App")

# CORS middleware for local testing/cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ADK Runner for local execution
adk_runner = Runner(
    app_name="local_agent_web_ui",
    agent=root_agent,
    artifact_service=InMemoryArtifactService(),
    session_service=InMemorySessionService(),
    memory_service=InMemoryMemoryService(),
    credential_service=InMemoryCredentialService(),
    auto_create_session=True,
)

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    payload = await request.json()
    message_text = payload.get("message", "")
    session_id = payload.get("session_id") or str(uuid.uuid4())
    
    logger.info(f"Received chat request: session_id={session_id}, query={message_text}")
    
    new_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part.from_text(text=message_text)]
    )
    
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for event in adk_runner.run_async(
                user_id="default_web_user",
                session_id=session_id,
                new_message=new_message
            ):
                text_content = ""
                if event.content and event.content.parts:
                    text_content = "".join(p.text for p in event.content.parts if p.text)
                
                logger.info(f"YIELDING EVENT: author={event.author}, text={repr(text_content)}, partial={event.partial}")
                # Format event update to client
                update = {
                    "author": event.author or "assistant",
                    "text": text_content,
                    "partial": event.partial,
                    "session_id": session_id,
                }
                
                if event.error_message:
                    update["error"] = event.error_message
                
                yield f"data: {json.dumps(update)}\n\n"
                
        except Exception as e:
            logger.error(f"Error during agent run execution: {e}", exc_info=True)
            error_update = {
                "author": "system",
                "text": f"An error occurred while executing the agent request: {e}",
                "partial": False,
                "error": str(e)
            }
            yield f"data: {json.dumps(error_update)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Serve UI static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Default port 8080 is standard for Cloud Run target
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
