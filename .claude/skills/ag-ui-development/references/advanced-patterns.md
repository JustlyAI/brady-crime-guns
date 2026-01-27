# Advanced AG-UI Patterns

Advanced patterns for state management, error handling, streaming, and production deployment.

## State Management Patterns

### State with Validation
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class ValidatedState(BaseModel):
    """State with automatic validation."""
    
    counter: int = Field(ge=0, le=100, description="Counter 0-100")
    status: Literal["active", "paused", "completed"]
    user_id: str = Field(pattern=r'^[a-zA-Z0-9_-]+$')
    items: list[str] = Field(max_length=50)
    
    @field_validator('items')
    def validate_items(cls, v):
        if not all(len(item) > 0 for item in v):
            raise ValueError("Empty items not allowed")
        return v
```

### State Snapshots vs Deltas

**Use snapshots** when:
- Sending initial state
- State changes are large
- Simplicity is preferred

```python
from ag_ui.core import StateSnapshotEvent, EventType

@agent.tool
async def reset_state(
    ctx: RunContext[StateDeps[TaskState]]
) -> StateSnapshotEvent:
    """Reset state and send full snapshot."""
    ctx.deps.state.tasks = []
    ctx.deps.state.completed = []
    
    return StateSnapshotEvent(
        type=EventType.STATE_SNAPSHOT,
        snapshot=ctx.deps.state.model_dump()
    )
```

**Use deltas** when:
- Making small incremental changes
- Minimizing network traffic
- Precise updates needed

```python
from ag_ui.core import StateDeltaEvent

@agent.tool
async def update_task_status(
    ctx: RunContext[StateDeps[TaskState]],
    index: int,
    completed: bool
) -> StateDeltaEvent:
    """Update single field using delta."""
    ctx.deps.state.completed[index] = completed
    
    return StateDeltaEvent(
        type=EventType.STATE_DELTA,
        delta=[{
            "op": "replace",
            "path": f"/completed/{index}",
            "value": completed
        }]
    )
```

### JSON Patch Operations

```python
# Replace value
{"op": "replace", "path": "/counter", "value": 10}

# Add to array
{"op": "add", "path": "/items/-", "value": "new_item"}

# Add at specific index
{"op": "add", "path": "/items/0", "value": "first_item"}

# Remove from array
{"op": "remove", "path": "/items/2"}

# Remove field
{"op": "remove", "path": "/optional_field"}

# Move value
{"op": "move", "from": "/items/0", "path": "/items/3"}

# Copy value
{"op": "copy", "from": "/counter", "path": "/backup_counter"}

# Test (conditional operation)
{"op": "test", "path": "/counter", "value": 5}
```

### Complex State Updates

```python
@agent.tool
async def batch_update(
    ctx: RunContext[StateDeps[TaskState]],
    updates: list[dict]
) -> StateDeltaEvent:
    """Apply multiple state changes atomically."""
    
    operations = []
    
    for update in updates:
        if update["action"] == "add_task":
            ctx.deps.state.tasks.append(update["task"])
            ctx.deps.state.completed.append(False)
            operations.extend([
                {"op": "add", "path": "/tasks/-", "value": update["task"]},
                {"op": "add", "path": "/completed/-", "value": False}
            ])
        elif update["action"] == "complete":
            idx = update["index"]
            ctx.deps.state.completed[idx] = True
            operations.append({
                "op": "replace",
                "path": f"/completed/{idx}",
                "value": True
            })
    
    return StateDeltaEvent(
        type=EventType.STATE_DELTA,
        delta=operations
    )
```

## Error Handling Patterns

### Comprehensive Error Stream

```python
from ag_ui.core import RunErrorEvent
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

async def robust_event_generator(input_data: RunAgentInput):
    encoder = EventEncoder()
    
    try:
        # Validate input
        if not input_data.messages:
            raise ValueError("No messages provided")
        
        if not input_data.thread_id or not input_data.run_id:
            raise ValueError("Missing thread_id or run_id")
        
        # Start run
        yield encoder.encode(RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
        ))
        
        # Process agent logic
        async for event in agent.run_stream(input_data):
            yield encoder.encode(event)
        
        # Success
        yield encoder.encode(RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id,
            result={"status": "success"}
        ))
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        yield encoder.encode(RunErrorEvent(
            type=EventType.RUN_ERROR,
            message=f"Validation error: {str(e)}",
            code="VALIDATION_ERROR"
        ))
        
    except TimeoutError:
        logger.error("Request timeout")
        yield encoder.encode(RunErrorEvent(
            type=EventType.RUN_ERROR,
            message="Request timeout exceeded",
            code="TIMEOUT"
        ))
        
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        yield encoder.encode(RunErrorEvent(
            type=EventType.RUN_ERROR,
            message="Insufficient permissions",
            code="PERMISSION_DENIED"
        ))
        
    except Exception as e:
        logger.exception("Unexpected error in agent execution")
        yield encoder.encode(RunErrorEvent(
            type=EventType.RUN_ERROR,
            message=f"Internal error: {str(e)}",
            code="INTERNAL_ERROR"
        ))
```

### Tool-Level Error Handling

```python
from pydantic_ai import ToolReturn

@agent.tool
async def resilient_operation(
    ctx: RunContext,
    data: dict
) -> ToolReturn:
    """Tool with detailed error handling."""
    
    try:
        # Validation
        if "required_field" not in data:
            return ToolReturn(
                return_value={
                    "success": False,
                    "error": "Missing required_field"
                }
            )
        
        # Risky operation
        result = await external_api_call(data)
        
        return ToolReturn(
            return_value={
                "success": True,
                "result": result
            }
        )
        
    except APIError as e:
        logger.error(f"API error: {e}")
        return ToolReturn(
            return_value={
                "success": False,
                "error": f"API error: {e.message}",
                "retry_after": e.retry_after
            }
        )
        
    except Exception as e:
        logger.exception("Unexpected tool error")
        return ToolReturn(
            return_value={
                "success": False,
                "error": "Internal error occurred"
            }
        )
```

## Streaming Patterns

### Progressive Streaming with Backpressure

```python
import asyncio

async def streaming_with_backpressure(input_data: RunAgentInput):
    """Stream with queue-based backpressure."""
    
    encoder = EventEncoder()
    event_queue = asyncio.Queue(maxsize=100)
    
    async def producer():
        """Generate events in background."""
        try:
            # Generate events
            for event in generate_events(input_data):
                await event_queue.put(event)
            
            # Signal completion
            await event_queue.put(None)
            
        except Exception as e:
            await event_queue.put(e)
    
    # Start producer
    producer_task = asyncio.create_task(producer())
    
    try:
        while True:
            event = await event_queue.get()
            
            if event is None:
                break
            
            if isinstance(event, Exception):
                yield encoder.encode(RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    message=str(event),
                    code="INTERNAL_ERROR"
                ))
                break
            
            yield encoder.encode(event)
            await asyncio.sleep(0)  # Let event loop process
    
    finally:
        await producer_task
```

### Chunked Streaming

```python
async def chunked_streaming(content: str, chunk_size: int = 10):
    """Stream content in fixed-size chunks."""
    
    encoder = EventEncoder()
    message_id = str(uuid.uuid4())
    
    yield encoder.encode(TextMessageStartEvent(
        type=EventType.TEXT_MESSAGE_START,
        message_id=message_id,
        role="assistant"
    ))
    
    # Stream in chunks
    for i in range(0, len(content), chunk_size):
        chunk = content[i:i + chunk_size]
        yield encoder.encode(TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=chunk
        ))
        await asyncio.sleep(0.01)  # Simulate streaming delay
    
    yield encoder.encode(TextMessageEndEvent(
        type=EventType.TEXT_MESSAGE_END,
        message_id=message_id
    ))
```

### Rate-Limited Streaming

```python
import time
from collections import deque

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: float, capacity: float):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
    
    async def acquire(self):
        """Wait until token available."""
        while True:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            
            await asyncio.sleep(0.01)

async def rate_limited_streaming(events, rate=10.0):
    """Stream events with rate limiting."""
    
    limiter = RateLimiter(rate=rate, capacity=rate * 2)
    encoder = EventEncoder()
    
    for event in events:
        await limiter.acquire()
        yield encoder.encode(event)
```

## Production Patterns

### Health Checks

```python
from fastapi import FastAPI, status
from datetime import datetime

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health/ready")
async def readiness_check():
    """Readiness check with dependency verification."""
    try:
        # Check database
        await database.ping()
        
        # Check external API
        await external_api.health_check()
        
        return {
            "status": "ready",
            "dependencies": {
                "database": "ok",
                "external_api": "ok"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "error": str(e)
            }
        )
```

### Metrics and Monitoring

```python
from prometheus_client import Counter, Histogram, generate_latest
import time

# Metrics
request_count = Counter('ag_ui_requests_total', 'Total requests')
request_duration = Histogram('ag_ui_request_duration_seconds', 'Request duration')
error_count = Counter('ag_ui_errors_total', 'Total errors', ['error_type'])

@app.post("/")
async def monitored_endpoint(input_data: RunAgentInput):
    """Endpoint with metrics."""
    
    request_count.inc()
    start_time = time.time()
    
    try:
        async def event_generator():
            try:
                async for event in generate_events(input_data):
                    yield event
            except Exception as e:
                error_count.labels(error_type=type(e).__name__).inc()
                raise
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    
    finally:
        request_duration.observe(time.time() - start_time)

@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(
        generate_latest(),
        media_type="text/plain"
    )
```

### Structured Logging

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    """JSON structured logging."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        handler.setFormatter(self.JsonFormatter())
        self.logger.addHandler(handler)
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name
            }
            
            if hasattr(record, 'extra'):
                log_data.update(record.extra)
            
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_data)
    
    def info(self, message, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def error(self, message, **kwargs):
        self.logger.error(message, extra=kwargs)

# Usage
logger = StructuredLogger(__name__)

async def logged_endpoint(input_data: RunAgentInput):
    logger.info(
        "Request received",
        thread_id=input_data.thread_id,
        run_id=input_data.run_id,
        message_count=len(input_data.messages)
    )
    
    try:
        # Process request
        result = await process(input_data)
        
        logger.info(
            "Request completed",
            thread_id=input_data.thread_id,
            run_id=input_data.run_id,
            duration_ms=result.duration
        )
        
    except Exception as e:
        logger.error(
            "Request failed",
            thread_id=input_data.thread_id,
            run_id=input_data.run_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

### Request Timeouts

```python
import asyncio

async def timeout_wrapper(
    coro,
    timeout: float = 30.0
):
    """Wrap coroutine with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation exceeded {timeout}s timeout")

async def endpoint_with_timeout(input_data: RunAgentInput):
    """Endpoint with request timeout."""
    
    try:
        async def event_generator():
            # Wrap each operation with timeout
            events = await timeout_wrapper(
                generate_events(input_data),
                timeout=30.0
            )
            
            for event in events:
                yield encoder.encode(event)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
        
    except TimeoutError as e:
        return StreamingResponse(
            single_error_event(str(e), "TIMEOUT"),
            media_type="text/event-stream"
        )
```

### Connection Management

```python
from contextlib import asynccontextmanager

class ConnectionPool:
    """Manage database connections."""
    
    def __init__(self, max_connections: int = 10):
        self.pool = None
        self.max_connections = max_connections
    
    async def connect(self):
        """Initialize connection pool."""
        self.pool = await create_pool(
            max_size=self.max_connections
        )
    
    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool."""
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)

# FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    pool = ConnectionPool()
    await pool.connect()
    app.state.db_pool = pool
    
    yield
    
    # Shutdown
    await pool.disconnect()

app = FastAPI(lifespan=lifespan)

@app.post("/")
async def endpoint(input_data: RunAgentInput, request: Request):
    """Use connection pool from app state."""
    async with request.app.state.db_pool.acquire() as conn:
        results = await conn.query("SELECT * FROM data")
        # Process results
```

## Testing Patterns

### Mock Streaming Events

```python
import pytest

@pytest.fixture
async def mock_event_stream():
    """Create mock event stream for testing."""
    
    async def stream():
        yield RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id="test",
            run_id="run_1"
        )
        
        message_id = "msg_1"
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant"
        )
        
        for word in ["Hello", " ", "world"]:
            yield TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=word
            )
        
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        
        yield RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id="test",
            run_id="run_1"
        )
    
    return stream()

@pytest.mark.asyncio
async def test_event_processing(mock_event_stream):
    """Test event stream processing."""
    events = []
    async for event in mock_event_stream:
        events.append(event)
    
    assert len(events) == 6
    assert events[0].type == EventType.RUN_STARTED
    assert events[-1].type == EventType.RUN_FINISHED
```

### Integration Tests

```python
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

def test_full_conversation(client):
    """Test complete conversation flow."""
    
    response = client.post(
        "/",
        json={
            "thread_id": "test_thread",
            "run_id": "run_1",
            "messages": [
                {"id": "1", "role": "user", "content": "Hello"}
            ],
            "tools": [],
            "context": [],
            "forwarded_props": {},
            "state": {}
        },
        headers={"accept": "text/event-stream"}
    )
    
    assert response.status_code == 200
    
    # Parse events
    events = parse_sse_events(response.text)
    
    # Verify event sequence
    assert events[0]["type"] == "RUN_STARTED"
    assert any(e["type"] == "TEXT_MESSAGE_CONTENT" for e in events)
    assert events[-1]["type"] == "RUN_FINISHED"
```
