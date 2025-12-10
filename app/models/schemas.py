"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class RunStatus(str, Enum):
    """Workflow run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class NodeDefinition(BaseModel):
    """Definition of a workflow node."""
    name: str = Field(..., description="Unique name of the node")
    function: str = Field(..., description="Name of the function to execute")
    description: Optional[str] = Field(None, description="Description of what this node does")


class EdgeDefinition(BaseModel):
    """Definition of an edge (transition) between nodes."""
    from_node: str = Field(..., description="Source node name")
    to_node: str = Field(..., description="Destination node name")
    condition: Optional[str] = Field(None, description="Optional condition for conditional routing")


class GraphCreate(BaseModel):
    """Request model for creating a new graph."""
    name: str = Field(..., description="Name of the graph")
    description: Optional[str] = Field(None, description="Description of the graph")
    nodes: List[NodeDefinition] = Field(..., description="List of nodes in the graph")
    edges: List[EdgeDefinition] = Field(..., description="List of edges connecting nodes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "code_review_workflow",
                "description": "A workflow for reviewing code quality",
                "nodes": [
                    {"name": "extract_functions", "function": "extract_functions"},
                    {"name": "check_complexity", "function": "check_complexity"}
                ],
                "edges": [
                    {"from_node": "extract_functions", "to_node": "check_complexity"}
                ]
            }
        }


class GraphResponse(BaseModel):
    """Response model for graph creation."""
    graph_id: str = Field(..., description="Unique identifier of the created graph")
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class GraphDetail(BaseModel):
    """Detailed graph information."""
    graph_id: str
    name: str
    description: Optional[str]
    nodes: List[NodeDefinition]
    edges: List[EdgeDefinition]
    created_at: datetime
    updated_at: datetime


class RunRequest(BaseModel):
    """Request model for running a workflow."""
    graph_id: str = Field(..., description="ID of the graph to run")
    initial_state: Dict[str, Any] = Field(..., description="Initial state for the workflow")
    
    class Config:
        json_schema_extra = {
            "example": {
                "graph_id": "123e4567-e89b-12d3-a456-426614174000",
                "initial_state": {
                    "code": "def example(): pass",
                    "threshold": 70,
                    "max_iterations": 3
                }
            }
        }


class ExecutionLogResponse(BaseModel):
    """Response model for execution log entry."""
    node_name: str
    step_number: int
    state_before: Dict[str, Any]
    state_after: Dict[str, Any]
    executed_at: datetime
    error: Optional[str]
    
    class Config:
        from_attributes = True


class RunResponse(BaseModel):
    """Response model for workflow execution."""
    run_id: str = Field(..., description="Unique identifier of the run")
    graph_id: str
    status: RunStatus
    final_state: Dict[str, Any] = Field(..., description="Final state after execution")
    execution_logs: List[ExecutionLogResponse] = Field(..., description="Step-by-step execution logs")
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


class StateResponse(BaseModel):
    """Response model for getting current state."""
    run_id: str
    graph_id: str
    status: RunStatus
    current_state: Dict[str, Any]
    current_node: Optional[str]
    execution_logs: List[ExecutionLogResponse]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True
