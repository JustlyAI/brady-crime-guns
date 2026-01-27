---
name: ag-ui-development
description: Build production-ready AG-UI protocol servers in Python with Claude integration via Pydantic AI. Use when developing agentic systems with real-time streaming interfaces, building chatbots with tool calling, implementing agent-to-UI communication with state management, or creating FastAPI endpoints that integrate Claude models through the Anthropic API. Covers event streaming, server setup, tool integration, state management, and Pydantic AI adapter patterns.
---

# AG-UI Development

## Overview

Build AG-UI (Agent-User Interaction Protocol) servers in Python that connect AI agents to streaming user interfaces. AG-UI standardizes real-time agent communication with features like token-by-token streaming, bidirectional state synchronization, tool calling, and human-in-the-loop workflows.

**Key capabilities:**
- FastAPI server setup with SSE streaming
- Claude integration via Pydantic AI
- Tool calling (server-side and frontend)
- State management with Pydantic models
- Proper event sequencing and error handling

## Quick Start

**Minimal AG-UI server with Claude:**

```python
from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    instructions='You are a helpful assistant!'
)

app = AGUIApp(agent)
# Run with: uvicorn server:app --port 8000
```

**Installation:**
```bash
pip install 'pydantic-ai-slim[ag-ui]' fastapi uvicorn
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
```

See `scripts/minimal_server.py` for runnable example.

## Core Workflow

### 1. Server Setup

Create FastAPI endpoint that accepts `RunAgentInput` and returns Server-Sent Events:

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from ag_ui.core import RunAgentInput, EventType, EventEncoder
from ag_ui.core import RunStartedEvent, TextMessageStartEvent, 
    TextMessageContentEvent, TextMessageEndEvent, RunFinishedEvent

app = FastAPI()

@app.post("/")
async def agent_endpoint(input_data: RunAgentInput):
    async def event_generator():
        encoder = EventEncoder()
        
        # 1. Signal run start
        yield encoder.encode(RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
        ))
        
        # 2. Start message
        message_id = str(uuid.uuid4())
        yield encoder.encode(TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant"
        ))
        
        # 3. Stream content chunks
        yield encoder.encode(TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta="Hello, world!"
        ))
        
        # 4. End message
        yield encoder.encode(TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        ))
        
        # 5. Complete run
        yield encoder.encode(RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
        ))
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### 2. Claude Integration via Pydantic AI

**Recommended pattern** - Use Pydantic AI's AG-UI support for Claude integration:

```python
from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    instructions='System prompt here',
    model_settings={'max_tokens': 2000, 'temperature': 0.7}
)

@app.post('/')
async def run_agent(request: Request):
    run_input = AGUIAdapter.build_run_input(await request.body())
    adapter = AGUIAdapter(agent=agent, run_input=run_input)
    
    event_stream = adapter.run_stream()
    sse_stream = adapter.encode_stream(event_stream)
    
    return StreamingResponse(sse_stream, media_type="text/event-stream")
```

**Benefits:** Automatic event handling, proper error handling, conversation history management, and native Claude API integration.

### 3. Tool Integration

Define server-side tools with `@agent.tool`:

```python
from pydantic_ai import Agent, RunContext
from datetime import datetime

agent = Agent('anthropic:claude-sonnet-4-20250514')

@agent.tool_plain
async def get_current_time(timezone: str = 'UTC') -> str:
    """Get current time in specified timezone.
    
    Args:
        timezone: Timezone name (e.g., 'America/New_York')
    
    Returns:
        Current time in ISO format
    """
    tz = ZoneInfo(timezone)
    return datetime.now(tz=tz).isoformat()

@agent.tool
async def search_database(
    ctx: RunContext,
    query: str,
    limit: int = 10
) -> dict:
    """Search database for information."""
    results = await database.search(query, limit=limit)
    return {"results": results, "count": len(results)}
```

**Tool requirements:**
- Clear, descriptive name
- Detailed docstring explaining functionality
- Proper type hints for parameters
- Return type annotation

### 4. State Management

Implement shared state between UI and agent:

```python
from pydantic import BaseModel
from pydantic_ai.ui import StateDeps
from pydantic_ai.ui.ag_ui.app import AGUIApp

class AppState(BaseModel):
    """Shared state between UI and agent."""
    tasks: list[str] = []
    completed: list[bool] = []

agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    deps_type=StateDeps[AppState]
)

@agent.tool
async def add_task(
    ctx: RunContext[StateDeps[AppState]],
    task: str
) -> str:
    """Add task to shared state."""
    ctx.deps.state.tasks.append(task)
    ctx.deps.state.completed.append(False)
    return f"Added: {task}"

# Initialize with default state
app = AGUIApp(agent, deps=StateDeps(AppState()))
```

## Event Sequencing

**Critical rule:** Always follow this event order:

```python
# ✓ CORRECT sequence
RunStartedEvent
  → TextMessageStartEvent
    → TextMessageContentEvent (multiple)
  → TextMessageEndEvent
→ RunFinishedEvent

# ✗ WRONG - Missing TextMessageStartEvent
RunStartedEvent
→ TextMessageContentEvent  # ERROR!
→ RunFinishedEvent
```

**Event lifecycle patterns:**

1. **Simple text response:**
   ```
   RUN_STARTED → TEXT_MESSAGE_START → TEXT_MESSAGE_CONTENT → TEXT_MESSAGE_END → RUN_FINISHED
   ```

2. **Tool call with response:**
   ```
   RUN_STARTED 
   → TOOL_CALL_START → TOOL_CALL_ARGS → TOOL_CALL_END → TOOL_CALL_RESULT
   → TEXT_MESSAGE_START → TEXT_MESSAGE_CONTENT → TEXT_MESSAGE_END
   → RUN_FINISHED
   ```

3. **Error handling:**
   ```
   RUN_STARTED → [some events] → RUN_ERROR
   ```

See `references/event-types.md` for complete event reference.

## Common Patterns

### Error Handling in Streams

```python
from ag_ui.core import RunErrorEvent

async def robust_event_generator(input_data: RunAgentInput):
    encoder = EventEncoder()
    
    try:
        yield encoder.encode(RunStartedEvent(...))
        
        # Process agent logic
        async for event in agent.run_stream(input_data):
            yield encoder.encode(event)
        
        yield encoder.encode(RunFinishedEvent(...))
        
    except ValidationError as e:
        yield encoder.encode(RunErrorEvent(
            type=EventType.RUN_ERROR,
            message=f"Validation error: {str(e)}",
            code="VALIDATION_ERROR"
        ))
    except Exception as e:
        logger.exception("Agent execution error")
        yield encoder.encode(RunErrorEvent(
            type=EventType.RUN_ERROR,
            message=f"Internal error: {str(e)}",
            code="INTERNAL_ERROR"
        ))
```

### Custom Events for Progress Updates

```python
from ag_ui.core import CustomEvent
from pydantic_ai import ToolReturn

@agent.tool
async def process_data(
    ctx: RunContext,
    data: list[dict]
) -> ToolReturn:
    """Process data with progress updates."""
    progress_events = []
    
    for i, item in enumerate(data):
        result = await process_item(item)
        
        progress_events.append(CustomEvent(
            type=EventType.CUSTOM,
            name='progress_update',
            value={
                'step': f'Processing item {i+1}',
                'percentage': int((i + 1) / len(data) * 100)
            }
        ))
    
    return ToolReturn(
        return_value=f"Processed {len(data)} items",
        metadata=progress_events
    )
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)
```

## Testing

**Quick test with curl:**

```bash
curl -N http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "thread_id": "test_thread",
    "run_id": "test_run",
    "tools": [],
    "context": [],
    "forwarded_props": {},
    "state": {}
  }'
```

**Automated testing:**

```python
from fastapi.testclient import TestClient
import json

def test_ag_ui_endpoint():
    client = TestClient(app)
    
    response = client.post(
        "/",
        json={
            "thread_id": "test",
            "run_id": "run_1",
            "messages": [{"id": "1", "role": "user", "content": "Hi"}],
            "tools": [],
            "context": [],
            "forwarded_props": {},
            "state": {}
        },
        headers={"accept": "text/event-stream"}
    )
    
    assert response.status_code == 200
    
    # Parse SSE events
    events = []
    for line in response.text.split('\n'):
        if line.startswith('data: '):
            events.append(json.loads(line[6:]))
    
    # Verify sequence
    assert events[0]["type"] == "RUN_STARTED"
    assert events[-1]["type"] == "RUN_FINISHED"
```

## Best Practices

1. **ID Management:** Generate unique UUIDs for message_id and tool_call_id, maintain consistency across related events

2. **Event Ordering:** Always emit events in correct sequence (start before content before end)

3. **State Validation:** Use Pydantic models for automatic state validation

4. **Error Handling:** Wrap event generation in try-except, emit RUN_ERROR on failures

5. **Logging:** Implement comprehensive logging for debugging production issues

6. **Async Patterns:** Use proper async generators with `yield`, include `await asyncio.sleep(0)` for event loop processing

7. **Tool Documentation:** Write detailed docstrings with type hints for tools

8. **Testing:** Test with both curl and automated tests before deployment

## Common Pitfalls

❌ **Wrong event field names:**
```python
yield {"type": "TEXT_MESSAGE_CONTENT", "text": "Hello"}  # Wrong!
```

✓ **Use proper event classes:**
```python
yield encoder.encode(TextMessageContentEvent(
    type=EventType.TEXT_MESSAGE_CONTENT,
    message_id=message_id,
    delta="Hello"  # Correct field name
))
```

❌ **Buffered streaming:**
```python
async def bad_stream():
    events = []
    for e in generate_events():
        events.append(e)
    return events  # Sends all at once
```

✓ **True streaming:**
```python
async def good_stream():
    async for event in generate_events():
        yield encoder.encode(event)
        await asyncio.sleep(0)
```

## Resources

### scripts/
- `minimal_server.py` - Minimal AG-UI + Claude server
- `complete_example.py` - Full production example with tools and state

### references/
- `event-types.md` - Complete event type reference
- `pydantic-ai-integration.md` - Detailed Pydantic AI patterns
- `advanced-patterns.md` - State management and error handling

Run scripts directly:
```bash
python scripts/minimal_server.py
python scripts/complete_example.py
```

Load references when needed:
```python
view('/home/claude/ag-ui-development/references/event-types.md')
```
