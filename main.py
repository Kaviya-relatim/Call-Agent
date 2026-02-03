"""
Combined Entry Point - Runs both Token Server and Voice Agent
==============================================================

This runs:
1. FastAPI token server (for /call endpoint) on port 10000
2. LiveKit voice agent (to handle conversations)

Both run in the same process to avoid needing a separate background worker.
"""

import os
import asyncio
import threading
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("relatim-combined")

def run_token_server():
    """Run the FastAPI token server in a separate thread"""
    import uvicorn
    from token_server import app
    
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting token server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def run_voice_agent():
    """Run the LiveKit voice agent"""
    from livekit import agents
    from livekit.agents import (
        AgentSession,
        Agent,
        JobContext,
        WorkerOptions,
        cli,
    )
    from livekit.plugins import deepgram, silero, cartesia, groq
    
    SYSTEM_PROMPT = """You are Relatim Voice Assistant, an AI helper for a field service management application.
Your role is to help users navigate and manage their service jobs through voice commands.

You can help users with:
1. Navigating to different job views (scheduled, reported, in progress, completed, billed)
2. Finding specific jobs or customers
3. Updating job statuses
4. Getting summaries of their workload
5. General questions about using the app

Keep your responses concise and conversational since this is a voice interface.
Be helpful, efficient, and professional."""

    def prewarm(proc: agents.JobProcess):
        proc.userdata["vad"] = silero.VAD.load()
        logger.info("Agent prewarmed with VAD model")

    class RelatimAssistant(Agent):
        def __init__(self):
            super().__init__(instructions=SYSTEM_PROMPT)

    async def entrypoint(ctx: JobContext):
        logger.info(f"Agent starting for room: {ctx.room.name}")
        
        # Check if this is an outbound call
        is_outbound = False
        phone_number = None
        if ctx.job.metadata:
            try:
                import json
                metadata = json.loads(ctx.job.metadata)
                is_outbound = metadata.get("outbound", False)
                phone_number = metadata.get("phone_number")
                logger.info(f"Outbound call to: {phone_number}")
            except:
                pass
        
        await ctx.connect()
        
        session = AgentSession(
            stt=deepgram.STT(
                api_key=os.getenv("DEEPGRAM_API_KEY"),
                model="nova-2",
                language="en",
            ),
            llm=groq.LLM(
                model="llama-3.3-70b-versatile",
                api_key=os.getenv("GROQ_API_KEY"),
            ),
            tts=cartesia.TTS(
                api_key=os.getenv("CARTESIA_API_KEY"),
            ),
            vad=silero.VAD.load(),
        )
        
        await session.start(
            room=ctx.room,
            agent=RelatimAssistant(),
        )
        
        if is_outbound:
            await session.generate_reply(
                instructions="Introduce yourself as the Relatim assistant calling about their service. Ask if this is a good time to talk."
            )
        else:
            await session.generate_reply(
                instructions="Greet the user warmly and ask how you can help them today."
            )
        
        logger.info(f"Agent ready (outbound={is_outbound})")

    # Start agent with WorkerOptions
    logger.info("Starting voice agent...")
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="relatim-voice-agent",
        )
    )

if __name__ == "__main__":
    # Start token server in a background thread
    server_thread = threading.Thread(target=run_token_server, daemon=True)
    server_thread.start()
    logger.info("Token server thread started")
    
    # Run voice agent in main thread (it has its own event loop)
    run_voice_agent()
