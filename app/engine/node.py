"""
Node abstraction for workflow steps.

Each node is a unit of work that reads and modifies the workflow state.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Any
from app.engine.state import WorkflowState


class Node(ABC):
    """
    Abstract base class for workflow nodes.
    
    A node represents a single step in the workflow that processes the state.
    """
    
    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize a node.
        
        Args:
            name: Unique name of the node
            description: Optional description of what the node does
        """
        self.name = name
        self.description = description or f"Node: {name}"
    
    @abstractmethod
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the node's logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Modified workflow state
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class FunctionNode(Node):
    """
    A node that wraps a Python function.
    
    The function should accept a state dictionary and return a modified state dictionary.
    """
    
    def __init__(
        self,
        name: str,
        function: Callable[[Dict[str, Any]], Dict[str, Any]],
        description: Optional[str] = None
    ):
        """
        Initialize a function node.
        
        Args:
            name: Unique name of the node
            function: Function to execute (takes state dict, returns state dict)
            description: Optional description
        """
        super().__init__(name, description)
        self.function = function
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the wrapped function.
        
        Args:
            state: Current workflow state
            
        Returns:
            Modified workflow state
        """
        # Get current state as dict
        state_dict = state.to_dict()
        
        # Execute function
        result = self.function(state_dict)
        
        # Return updated state
        return WorkflowState.from_dict(result)
