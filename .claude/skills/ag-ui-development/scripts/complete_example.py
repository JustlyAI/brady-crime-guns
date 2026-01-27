#!/usr/bin/env python3
"""
Complete AG-UI Server Example with Tools and State

A production-ready AG-UI server demonstrating:
- Claude integration via Pydantic AI
- Server-side tool calling
- Shared state management
- Error handling
- Health checks
- CORS configuration

Installation:
    pip install 'pydantic-ai-slim[ag-ui]' fastapi uvicorn

Configuration:
    export ANTHROPIC_API_KEY="sk-ant-xxxxx"

Usage:
    python complete_example.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.ui import StateDeps
from pydantic_ai.ui.ag_ui.app import AGUIApp
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Define shared state
class TaskState(BaseModel):
    """Shared state for task management."""
    project_name: str = ""
    tasks: list[str] = []
    completed: list[bool] = []
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# Create Claude agent with tools
agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    instructions="""You are a helpful project management assistant.
    Help users organize their projects, track tasks, and take notes.
    Be proactive in suggesting improvements and next steps.""",
    deps_type=StateDeps[TaskState],
    model_settings={
        'max_tokens': 2000,
        'temperature': 0.7
    }
)


@agent.tool
async def add_task(
    ctx: RunContext[StateDeps[TaskState]],
    task_description: str
) -> str:
    """Add a new task to the project.
    
    Args:
        task_description: Clear description of the task to add
    
    Returns:
        Confirmation message with task number
    """
    ctx.deps.state.tasks.append(task_description)
    ctx.deps.state.completed.append(False)
    
    task_num = len(ctx.deps.state.tasks)
    logger.info(f"Added task #{task_num}: {task_description}")
    
    return f"Added task #{task_num}: {task_description}"


@agent.tool
async def complete_task(
    ctx: RunContext[StateDeps[TaskState]],
    task_index: int
) -> str:
    """Mark a task as completed.
    
    Args:
        task_index: Task number to complete (1-based, e.g., 1 for first task)
    
    Returns:
        Confirmation message
    """
    # Convert to 0-based index
    idx = task_index - 1
    
    if 0 <= idx < len(ctx.deps.state.tasks):
        ctx.deps.state.completed[idx] = True
        task = ctx.deps.state.tasks[idx]
        logger.info(f"Completed task #{task_index}: {task}")
        return f"✓ Marked task #{task_index} as complete: {task}"
    
    return f"Error: Task #{task_index} not found. Project has {len(ctx.deps.state.tasks)} tasks."


@agent.tool
async def list_tasks(
    ctx: RunContext[StateDeps[TaskState]]
) -> dict:
    """Get a list of all tasks with their completion status.
    
    Returns:
        Dictionary with task lists and statistics
    """
    tasks = ctx.deps.state.tasks
    completed = ctx.deps.state.completed
    
    task_list = []
    for i, (task, done) in enumerate(zip(tasks, completed), 1):
        status = "✓" if done else "○"
        task_list.append(f"{i}. {status} {task}")
    
    return {
        "project": ctx.deps.state.project_name or "Unnamed Project",
        "tasks": task_list,
        "total": len(tasks),
        "completed": sum(completed),
        "pending": len(tasks) - sum(completed)
    }


@agent.tool
async def update_notes(
    ctx: RunContext[StateDeps[TaskState]],
    notes: str
) -> str:
    """Update project notes.
    
    Args:
        notes: New project notes or additional context
    
    Returns:
        Confirmation message
    """
    ctx.deps.state.notes = notes
    logger.info("Updated project notes")
    return "Project notes updated successfully"


@agent.tool
async def get_project_status(
    ctx: RunContext[StateDeps[TaskState]]
) -> dict:
    """Get comprehensive project status summary.
    
    Returns:
        Dictionary with project statistics and status
    """
    total_tasks = len(ctx.deps.state.tasks)
    completed_tasks = sum(ctx.deps.state.completed)
    
    completion_rate = (
        f"{completed_tasks/total_tasks*100:.1f}%" 
        if total_tasks > 0 
        else "0%"
    )
    
    return {
        "project_name": ctx.deps.state.project_name or "Unnamed Project",
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": total_tasks - completed_tasks,
        "completion_rate": completion_rate,
        "created_at": ctx.deps.state.created_at,
        "has_notes": len(ctx.deps.state.notes) > 0
    }


@agent.tool
async def set_project_name(
    ctx: RunContext[StateDeps[TaskState]],
    name: str
) -> str:
    """Set or update the project name.
    
    Args:
        name: New project name
    
    Returns:
        Confirmation message
    """
    ctx.deps.state.project_name = name
    logger.info(f"Set project name: {name}")
    return f"Project name set to: {name}"


@agent.tool_plain
async def get_current_time(timezone: str = 'UTC') -> str:
    """Get current time in specified timezone.
    
    Args:
        timezone: Timezone name (e.g., 'America/New_York', 'Europe/London')
    
    Returns:
        Current time in ISO format
    """
    try:
        tz = ZoneInfo(timezone)
        current = datetime.now(tz=tz)
        return current.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"Error: Invalid timezone '{timezone}'"


@agent.instructions
async def dynamic_instructions(
    ctx: RunContext[StateDeps[TaskState]]
) -> str:
    """Provide dynamic instructions based on current state."""
    total = len(ctx.deps.state.tasks)
    completed = sum(ctx.deps.state.completed)
    
    project_name = ctx.deps.state.project_name or "Unnamed Project"
    
    if total == 0:
        status_msg = "No tasks yet - help the user get started!"
    elif completed == total:
        status_msg = "All tasks complete! Celebrate and suggest next steps."
    else:
        status_msg = f"{completed}/{total} tasks completed - encourage progress!"
    
    return f"""
    Current Project: {project_name}
    Status: {status_msg}
    
    Help the user manage their project effectively. 
    - Be proactive in suggesting task breakdowns
    - Celebrate completed tasks
    - Suggest priorities when asked
    - Keep track of notes and context
    """


# Create AG-UI app with initial state
initial_state = TaskState(
    project_name="My New Project",
    created_at=datetime.now().isoformat()
)

app = AGUIApp(agent, deps=StateDeps(initial_state))


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ag-ui-task-manager",
        "model": "claude-sonnet-4",
        "timestamp": datetime.now().isoformat()
    }


# Readiness check
@app.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # In production, check dependencies here
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("AG-UI Task Management Server")
    print("=" * 60)
    print(f"Server starting on http://localhost:8000")
    print(f"Health check: http://localhost:8000/health")
    print(f"Model: Claude Sonnet 4")
    print("\nAvailable tools:")
    print("  - add_task: Add new tasks")
    print("  - complete_task: Mark tasks complete")
    print("  - list_tasks: View all tasks")
    print("  - get_project_status: Get project summary")
    print("  - set_project_name: Set project name")
    print("  - update_notes: Add project notes")
    print("  - get_current_time: Get current time")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
