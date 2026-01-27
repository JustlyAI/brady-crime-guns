# Pydantic AI Integration with AG-UI

Complete guide for integrating Claude through Pydantic AI with AG-UI protocol.

## Why Pydantic AI?

Claude Agent SDK doesn't natively support AG-UI protocol. Pydantic AI provides the best integration path with:
- Official AG-UI support
- Claude integration via Anthropic API
- Automatic event handling
- Built-in state management
- Comprehensive error handling

## Quick Setup

### Installation
```bash
pip install 'pydantic-ai-slim[ag-ui]' fastapi uvicorn
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
```

### Minimal Server
```python
from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui.app import AGUIApp

agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    instructions='You are a helpful assistant!'
)

app = AGUIApp(agent)
# Run: uvicorn server:app --port 8000
```

## Agent Configuration

### Model Selection
```python
from pydantic_ai import Agent

# Claude Sonnet 4 (balanced)
agent = Agent('anthropic:claude-sonnet-4-20250514')

# Claude Opus 4 (most capable)
agent = Agent('anthropic:claude-opus-4-20250514')

# Claude Haiku 4 (fast, efficient)
agent = Agent('anthropic:claude-haiku-4-20250514')
```

### Model Settings
```python
agent = Agent(
    model='anthropic:claude-sonnet-4-20250514',
    instructions='System prompt here',
    model_settings={
        'max_tokens': 4096,      # Response length limit
        'temperature': 0.7,      # Randomness (0-1)
        'top_p': 0.95           # Nucleus sampling
    }
)
```

### Dynamic Instructions
```python
from pydantic_ai import Agent, RunContext

agent = Agent('anthropic:claude-sonnet-4-20250514')

@agent.instructions
async def get_instructions(ctx: RunContext) -> str:
    """Generate instructions based on context."""
    return f"""
    You are a helpful assistant.
    Current time: {datetime.now().isoformat()}
    User context: {ctx.deps.user_info}
    """
```

## Tool Integration

### Simple Tools (@tool_plain)
```python
from pydantic_ai import Agent

agent = Agent('anthropic:claude-sonnet-4-20250514')

@agent.tool_plain
async def get_weather(location: str) -> dict:
    """Get current weather for a location.
    
    Args:
        location: City name or coordinates
    
    Returns:
        Weather data with temperature and conditions
    """
    # Implementation
    return {"temp": 72, "condition": "sunny"}
```

### Tools with Context (@tool)
```python
from pydantic_ai import RunContext

@agent.tool
async def search_database(
    ctx: RunContext,
    query: str,
    limit: int = 10
) -> dict:
    """Search database with user context.
    
    Args:
        query: Search query
        limit: Maximum results
    
    Returns:
        Search results
    """
    user_id = ctx.deps.user_id
    results = await db.search(query, user_id=user_id, limit=limit)
    return {"results": results, "count": len(results)}
```

### Tool Best Practices

**Comprehensive docstrings:**
```python
@agent.tool
async def calculate_discount(
    ctx: RunContext,
    price: float,
    discount_percent: int
) -> dict:
    """Calculate discounted price for a product.
    
    Applies percentage discount and returns both original 
    and discounted prices with savings amount.
    
    Args:
        price: Original price in USD (must be positive)
        discount_percent: Discount percentage (0-100)
    
    Returns:
        Dictionary with:
        - original_price: Original price
        - discounted_price: Price after discount
        - savings: Amount saved
    
    Example:
        calculate_discount(100.0, 20) 
        → {"original_price": 100.0, "discounted_price": 80.0, "savings": 20.0}
    """
    discount = price * (discount_percent / 100)
    return {
        "original_price": price,
        "discounted_price": price - discount,
        "savings": discount
    }
```

**Type hints for validation:**
```python
from typing import Literal

@agent.tool
async def set_status(
    ctx: RunContext,
    status: Literal["active", "paused", "completed"]  # Enum validation
) -> str:
    """Update status with validated choices."""
    ctx.deps.state.status = status
    return f"Status updated to {status}"
```

## State Management

### Define State Model
```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.ui import StateDeps
from pydantic_ai.ui.ag_ui.app import AGUIApp

class TaskState(BaseModel):
    """Shared state between UI and agent."""
    tasks: list[str] = []
    completed: list[bool] = []
    project_name: str = ""
```

### Create Agent with State
```python
agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    instructions='Task management assistant',
    deps_type=StateDeps[TaskState]
)
```

### Access State in Tools
```python
@agent.tool
async def add_task(
    ctx: RunContext[StateDeps[TaskState]],
    task: str
) -> str:
    """Add task to state."""
    ctx.deps.state.tasks.append(task)
    ctx.deps.state.completed.append(False)
    return f"Added: {task}"

@agent.tool
async def complete_task(
    ctx: RunContext[StateDeps[TaskState]],
    index: int
) -> str:
    """Mark task complete."""
    if 0 <= index < len(ctx.deps.state.tasks):
        ctx.deps.state.completed[index] = True
        return f"Completed: {ctx.deps.state.tasks[index]}"
    return "Invalid task index"
```

### Initialize App with State
```python
# Initialize with default state
app = AGUIApp(
    agent,
    deps=StateDeps(TaskState(project_name="My Project"))
)
```

### Dynamic Instructions from State
```python
@agent.instructions
async def task_instructions(
    ctx: RunContext[StateDeps[TaskState]]
) -> str:
    """Generate instructions based on current state."""
    total = len(ctx.deps.state.tasks)
    completed = sum(ctx.deps.state.completed)
    
    return f"""
    Project: {ctx.deps.state.project_name}
    Tasks: {completed}/{total} completed
    
    Help manage tasks and track progress.
    """
```

## Custom Dependencies

### Define Custom Deps
```python
from dataclasses import dataclass

@dataclass
class AppDeps:
    """Custom dependencies for agent."""
    user_id: str
    database: Database
    api_key: str

agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    deps_type=AppDeps
)

@agent.tool
async def fetch_user_data(ctx: RunContext[AppDeps]) -> dict:
    """Access custom dependencies."""
    return await ctx.deps.database.get_user(ctx.deps.user_id)
```

### Initialize with Custom Deps
```python
from pydantic_ai.ui.ag_ui.app import AGUIApp

deps = AppDeps(
    user_id="user_123",
    database=Database(),
    api_key="secret"
)

app = AGUIApp(agent, deps=deps)
```

## Advanced Patterns

### Multi-Step Tool Execution
```python
@agent.tool
async def complex_analysis(
    ctx: RunContext,
    data: list[dict]
) -> dict:
    """Multi-step analysis with intermediate results."""
    
    # Step 1: Preprocess
    cleaned = await preprocess_data(data)
    
    # Step 2: Analyze
    results = await analyze(cleaned)
    
    # Step 3: Generate report
    report = await generate_report(results)
    
    return {
        "analysis": results,
        "report": report,
        "data_points": len(data)
    }
```

### Tool with Progress Events
```python
from ag_ui.core import CustomEvent, EventType
from pydantic_ai import ToolReturn

@agent.tool
async def batch_process(
    ctx: RunContext,
    items: list[str]
) -> ToolReturn:
    """Process items with progress updates."""
    
    progress_events = []
    results = []
    
    for i, item in enumerate(items):
        result = await process_item(item)
        results.append(result)
        
        # Emit progress event
        progress_events.append(CustomEvent(
            type=EventType.CUSTOM,
            name='progress',
            value={
                'current': i + 1,
                'total': len(items),
                'percentage': int((i + 1) / len(items) * 100)
            }
        ))
    
    return ToolReturn(
        return_value={"processed": len(results), "results": results},
        metadata=progress_events
    )
```

### Error Handling in Tools
```python
@agent.tool
async def safe_operation(
    ctx: RunContext,
    data: dict
) -> dict:
    """Tool with comprehensive error handling."""
    
    try:
        # Validate input
        if not data:
            raise ValueError("Empty data provided")
        
        # Execute operation
        result = await risky_operation(data)
        
        return {"success": True, "result": result}
        
    except ValueError as e:
        return {"success": False, "error": f"Validation error: {str(e)}"}
    except Exception as e:
        logger.exception("Operation failed")
        return {"success": False, "error": "Internal error"}
```

## Full FastAPI Implementation

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    instructions='Helpful assistant',
    model_settings={'max_tokens': 2000}
)

app = FastAPI()

@app.post('/')
async def run_agent(request: Request):
    """AG-UI endpoint with Claude integration."""
    
    # Parse AG-UI request
    run_input = AGUIAdapter.build_run_input(await request.body())
    
    # Create adapter and stream events
    adapter = AGUIAdapter(agent=agent, run_input=run_input)
    event_stream = adapter.run_stream()
    sse_stream = adapter.encode_stream(event_stream)
    
    return StreamingResponse(
        sse_stream,
        media_type="text/event-stream"
    )
```

## Testing Pydantic AI Agents

```python
import pytest
from pydantic_ai import Agent

@pytest.mark.asyncio
async def test_agent_tool():
    agent = Agent('anthropic:claude-sonnet-4-20250514')
    
    @agent.tool
    async def add_numbers(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b
    
    # Test tool directly
    result = await add_numbers.run(5, 3)
    assert result == 8

@pytest.mark.asyncio
async def test_agent_with_state():
    from pydantic import BaseModel
    from pydantic_ai.ui import StateDeps
    
    class TestState(BaseModel):
        counter: int = 0
    
    agent = Agent(
        'anthropic:claude-sonnet-4-20250514',
        deps_type=StateDeps[TestState]
    )
    
    @agent.tool
    async def increment(ctx: RunContext[StateDeps[TestState]]) -> int:
        ctx.deps.state.counter += 1
        return ctx.deps.state.counter
    
    # Test with state
    state = TestState()
    result = await agent.run(
        "Increment the counter",
        deps=StateDeps(state)
    )
    assert state.counter == 1
```

## Deployment Considerations

### Environment Variables
```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# Optional
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
export LOG_LEVEL="INFO"
```

### Production Configuration
```python
from pydantic_ai import Agent
import os

agent = Agent(
    model='anthropic:claude-sonnet-4-20250514',
    instructions=os.getenv('AGENT_INSTRUCTIONS', 'Default instructions'),
    model_settings={
        'max_tokens': int(os.getenv('MAX_TOKENS', '4096')),
        'temperature': float(os.getenv('TEMPERATURE', '0.7'))
    }
)
```

### Health Checks
```python
from fastapi import FastAPI

app = AGUIApp(agent)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": "claude-sonnet-4",
        "timestamp": datetime.now().isoformat()
    }
```

## Resources

- Pydantic AI Docs: https://ai.pydantic.dev/
- Pydantic AI AG-UI: https://ai.pydantic.dev/ui/ag-ui/
- Claude API Docs: https://docs.anthropic.com/
- AG-UI Protocol: https://docs.ag-ui.com/
