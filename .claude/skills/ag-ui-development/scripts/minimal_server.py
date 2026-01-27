#!/usr/bin/env python3
"""
Minimal AG-UI Server with Claude Integration

A minimal working AG-UI protocol server using Pydantic AI and Claude.

Installation:
    pip install 'pydantic-ai-slim[ag-ui]' fastapi uvicorn

Configuration:
    export ANTHROPIC_API_KEY="sk-ant-xxxxx"

Usage:
    python minimal_server.py
    
    # Or with uvicorn directly:
    uvicorn minimal_server:app --host 0.0.0.0 --port 8000

Testing:
    curl -N http://localhost:8000/ \
      -H "Content-Type: application/json" \
      -H "Accept: text/event-stream" \
      -d '{"messages":[{"role":"user","content":"Hello!"}],"thread_id":"t1","run_id":"r1","tools":[],"context":[],"forwarded_props":{},"state":{}}'
"""

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

# Create Claude agent
agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    instructions='You are a helpful and friendly assistant!'
)

# Create AG-UI compatible ASGI app
app = AGUIApp(agent)

if __name__ == "__main__":
    import uvicorn
    print("Starting AG-UI server on http://localhost:8000")
    print("Press Ctrl+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=8000)
