# AG-UI Event Types Reference

Complete reference for all event types in the AG-UI protocol.

## Event Categories

### Lifecycle Events

**RunStartedEvent** - Signal agent execution begins
```python
from ag_ui.core import RunStartedEvent, EventType

RunStartedEvent(
    type=EventType.RUN_STARTED,
    thread_id: str,              # Conversation thread identifier
    run_id: str,                 # Unique run identifier
    parent_run_id: Optional[str] # For nested runs
)
```

**RunFinishedEvent** - Indicate successful completion
```python
RunFinishedEvent(
    type=EventType.RUN_FINISHED,
    thread_id: str,
    run_id: str,
    result: Optional[Any] = None  # Optional result payload
)
```

**RunErrorEvent** - Report errors during execution
```python
RunErrorEvent(
    type=EventType.RUN_ERROR,
    message: str,                    # Error description
    code: Optional[str] = None       # Error code (e.g., "VALIDATION_ERROR")
)
```

**StepStartedEvent / StepFinishedEvent** - Track processing steps
```python
StepStartedEvent(
    type=EventType.STEP_STARTED,
    step_name: str
)

StepFinishedEvent(
    type=EventType.STEP_FINISHED,
    step_name: str
)
```

### Text Message Events

**TextMessageStartEvent** - Initiate assistant message
```python
TextMessageStartEvent(
    type=EventType.TEXT_MESSAGE_START,
    message_id: str,                    # Unique message identifier
    role: Literal["assistant"]          # Always "assistant"
)
```

**TextMessageContentEvent** - Stream content chunks
```python
TextMessageContentEvent(
    type=EventType.TEXT_MESSAGE_CONTENT,
    message_id: str,                    # Links to TextMessageStartEvent
    delta: str                          # Content chunk (non-empty)
)
```

**TextMessageEndEvent** - Complete message
```python
TextMessageEndEvent(
    type=EventType.TEXT_MESSAGE_END,
    message_id: str                     # Links to TextMessageStartEvent
)
```

### Tool Call Events

**ToolCallStartEvent** - Begin tool execution
```python
ToolCallStartEvent(
    type=EventType.TOOL_CALL_START,
    tool_call_id: str,                      # Unique tool call identifier
    tool_call_name: str,                    # Tool function name
    parent_message_id: Optional[str] = None # Associated message
)
```

**ToolCallArgsEvent** - Stream tool arguments
```python
ToolCallArgsEvent(
    type=EventType.TOOL_CALL_ARGS,
    tool_call_id: str,              # Links to ToolCallStartEvent
    delta: str                      # JSON chunk of arguments
)
```

**ToolCallEndEvent** - Signal tool call completion
```python
ToolCallEndEvent(
    type=EventType.TOOL_CALL_END,
    tool_call_id: str               # Links to ToolCallStartEvent
)
```

**ToolCallResultEvent** - Return tool execution results
```python
ToolCallResultEvent(
    type=EventType.TOOL_CALL_RESULT,
    message_id: str,                # Unique message ID for result
    tool_call_id: str,              # Links to ToolCallStartEvent
    content: str,                   # Result content
    role: Optional[Literal["tool"]] = None
)
```

### State Management Events

**StateSnapshotEvent** - Send complete state
```python
StateSnapshotEvent(
    type=EventType.STATE_SNAPSHOT,
    snapshot: dict                  # Complete state object
)
```

**StateDeltaEvent** - Apply incremental changes
```python
StateDeltaEvent(
    type=EventType.STATE_DELTA,
    delta: List[dict]               # JSON Patch operations (RFC 6902)
)

# Example delta operations:
[
    {"op": "replace", "path": "/counter", "value": 5},
    {"op": "add", "path": "/items/-", "value": "new item"},
    {"op": "remove", "path": "/items/0"}
]
```

**MessagesSnapshotEvent** - Provide conversation history
```python
MessagesSnapshotEvent(
    type=EventType.MESSAGES_SNAPSHOT,
    messages: List[Message]         # Complete message history
)
```

### Special Events

**CustomEvent** - Application-specific events
```python
CustomEvent(
    type=EventType.CUSTOM,
    name: str,                      # Event name
    value: Any                      # Event payload
)

# Example: Progress updates
CustomEvent(
    type=EventType.CUSTOM,
    name="progress_update",
    value={"step": "Processing item 5/10", "percentage": 50}
)
```

**RawEvent** - Pass-through from external systems
```python
RawEvent(
    type=EventType.RAW,
    event: Any,                     # Original event data
    source: Optional[str] = None    # Source identifier
)
```

## Event Sequences

### Basic Text Response
```
RunStartedEvent
└─ TextMessageStartEvent
   ├─ TextMessageContentEvent (chunk 1)
   ├─ TextMessageContentEvent (chunk 2)
   ├─ TextMessageContentEvent (chunk n)
   └─ TextMessageEndEvent
└─ RunFinishedEvent
```

### Tool Call with Response
```
RunStartedEvent
└─ ToolCallStartEvent
   ├─ ToolCallArgsEvent
   └─ ToolCallEndEvent
└─ ToolCallResultEvent
└─ TextMessageStartEvent
   ├─ TextMessageContentEvent (synthesis)
   └─ TextMessageEndEvent
└─ RunFinishedEvent
```

### Multi-turn Conversation
```
RunStartedEvent
└─ TextMessageStartEvent
   ├─ TextMessageContentEvent
   └─ TextMessageEndEvent
└─ [User responds, new run starts]
└─ RunStartedEvent
   └─ TextMessageStartEvent
      ├─ TextMessageContentEvent
      └─ TextMessageEndEvent
   └─ RunFinishedEvent
```

### Error Handling
```
RunStartedEvent
└─ [Some processing events]
└─ RunErrorEvent (replaces RunFinishedEvent)
```

## Message Types in RunAgentInput

### UserMessage
```python
{
    "id": "msg_123",
    "role": "user",
    "content": "What's the weather?",
    "name": "john_doe"  # Optional
}
```

### AssistantMessage
```python
{
    "id": "msg_456",
    "role": "assistant",
    "content": "It's sunny!",  # Optional if using tool_calls
    "tool_calls": [            # Optional
        {
            "id": "call_123",
            "name": "get_weather",
            "arguments": '{"location": "NYC"}'
        }
    ]
}
```

### ToolMessage
```python
{
    "id": "msg_789",
    "role": "tool",
    "content": "72°F, sunny",
    "tool_call_id": "call_123"  # Links to tool call
}
```

### SystemMessage
```python
{
    "id": "msg_012",
    "role": "system",
    "content": "You are a helpful assistant."
}
```

## EventEncoder Usage

```python
from ag_ui.encoder import EventEncoder
from ag_ui.core import TextMessageContentEvent, EventType

encoder = EventEncoder()

event = TextMessageContentEvent(
    type=EventType.TEXT_MESSAGE_CONTENT,
    message_id="msg_123",
    delta="Hello!"
)

encoded = encoder.encode(event)
# Output: data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"msg_123","delta":"Hello!"}\n\n
```

## Best Practices

1. **Always maintain event order**: Start before content before end
2. **Use consistent IDs**: Same message_id across related events
3. **Non-empty deltas**: TextMessageContentEvent delta must not be empty string
4. **Link tool calls**: Use tool_call_id to connect results to calls
5. **Handle errors gracefully**: Emit RunErrorEvent on failures
6. **Include metadata**: Use optional fields for debugging (timestamps, etc.)
