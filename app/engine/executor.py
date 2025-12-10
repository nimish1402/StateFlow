"""
Workflow executor for running graphs.

Handles sequential execution, branching, and looping.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.engine.graph import WorkflowGraph
from app.engine.state import WorkflowState


class ExecutionStep:
    """Represents a single execution step in the workflow."""
    
    def __init__(
        self,
        node_name: str,
        step_number: int,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any],
        error: Optional[str] = None
    ):
        self.node_name = node_name
        self.step_number = step_number
        self.state_before = state_before
        self.state_after = state_after
        self.error = error
        self.executed_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_name": self.node_name,
            "step_number": self.step_number,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "error": self.error,
            "executed_at": self.executed_at.isoformat()
        }


class WorkflowExecutor:
    """
    Executes workflow graphs.
    
    Supports:
    - Sequential execution
    - Conditional branching
    - Loop detection and execution
    - Execution logging
    """
    
    def __init__(self, graph: WorkflowGraph, max_steps: int = 100):
        """
        Initialize executor.
        
        Args:
            graph: Workflow graph to execute
            max_steps: Maximum number of steps to prevent infinite loops
        """
        self.graph = graph
        self.max_steps = max_steps
        self.execution_log: List[ExecutionStep] = []
    
    def execute(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            initial_state: Initial state dictionary
            
        Returns:
            Dictionary with final state and execution log
            
        Raises:
            ValueError: If graph is invalid or execution fails
        """
        # Validate graph
        errors = self.graph.validate()
        if errors:
            raise ValueError(f"Invalid graph: {', '.join(errors)}")
        
        # Initialize state
        state = WorkflowState.from_dict(initial_state)
        current_node_name = self.graph.start_node
        step_number = 0
        
        # Clear execution log
        self.execution_log = []
        
        # Execute workflow
        while current_node_name is not None and step_number < self.max_steps:
            step_number += 1
            
            # Get current node
            node = self.graph.nodes[current_node_name]
            
            # Save state before execution
            state_before = state.to_dict()
            
            try:
                # Execute node
                state = node.execute(state)
                
                # Save state after execution
                state_after = state.to_dict()
                
                # Log execution
                step = ExecutionStep(
                    node_name=current_node_name,
                    step_number=step_number,
                    state_before=state_before,
                    state_after=state_after
                )
                self.execution_log.append(step)
                
                # Get next node
                current_node_name = self.graph.get_next_node(current_node_name, state)
                
            except Exception as e:
                # Log error
                step = ExecutionStep(
                    node_name=current_node_name,
                    step_number=step_number,
                    state_before=state_before,
                    state_after=state_before,  # State unchanged on error
                    error=str(e)
                )
                self.execution_log.append(step)
                
                raise ValueError(f"Error executing node '{current_node_name}': {str(e)}")
        
        # Check if we hit max steps (possible infinite loop)
        if step_number >= self.max_steps:
            raise ValueError(f"Workflow exceeded maximum steps ({self.max_steps}). Possible infinite loop.")
        
        return {
            "final_state": state.to_dict(),
            "execution_log": [step.to_dict() for step in self.execution_log],
            "steps_executed": step_number
        }
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get the execution log."""
        return [step.to_dict() for step in self.execution_log]
