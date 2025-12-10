"""
Workflow state management.

The state is a dictionary that flows through the workflow, being modified by each node.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from copy import deepcopy
import json


class WorkflowState(BaseModel):
    """
    Base class for workflow state.
    
    State is a flexible dictionary that can hold any data needed by the workflow.
    Each node reads from and writes to this state.
    """
    
    data: Dict[str, Any] = Field(default_factory=dict, description="State data")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the state."""
        self.data[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple values in the state."""
        self.data.update(updates)
    
    def copy(self) -> "WorkflowState":
        """Create a deep copy of the state."""
        return WorkflowState(data=deepcopy(self.data))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return self.data.copy()
    
    def to_json(self) -> str:
        """Convert state to JSON string."""
        return json.dumps(self.data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """Create state from dictionary."""
        return cls(data=data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowState":
        """Create state from JSON string."""
        return cls(data=json.loads(json_str))
    
    def __repr__(self) -> str:
        return f"WorkflowState({self.data})"
    
    class Config:
        arbitrary_types_allowed = True
