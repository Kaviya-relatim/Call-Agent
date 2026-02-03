#!/bin/bash

# Start token server in background
uvicorn token_server:app --host 0.0.0.0 --port $PORT &

# Start agent worker
python voice_agent.py start