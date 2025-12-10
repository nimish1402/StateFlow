"""
Workflow executor for running graphs.

Handles sequential execution, branching, and looping.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
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
    - WebSocket streaming (optional)
    """
    
    def __init__(self, graph: WorkflowGraph, max_steps: int = 100, run_id: Optional[str] = None):
        """
        Initialize executor.
        
        Args:
            graph: Workflow graph to execute
            max_steps: Maximum number of steps to prevent infinite loops
            run_id: Optional run ID for WebSocket streaming
        """
        self.graph = graph
        self.max_steps = max_steps
        self.execution_log: List[ExecutionStep] = []
        self.run_id = run_id
    
    async def _stream_log(self, message: dict):
        """
        Stream log message via WebSocket if run_id is set.
        
        Args:
            message: Log message dictionary
        """
        if self.run_id:
            try:
                from app.api.websocket import manager
                await manager.send_log(self.run_id, message)
            except Exception:
                # Silently fail if streaming not available
                pass
    
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
                
                # Stream log via WebSocket if run_id is set
                if self.run_id:
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Create task in existing loop
                            asyncio.create_task(self._stream_log({
                                "type": "step_complete",
                                "step_number": step_number,
                                "node_name": current_node_name,
                                "state_after": state_after,
                                "message": f"Completed step {step_number}: {current_node_name}"
                            }))
                        else:
                            # Run in new loop
                            loop.run_until_complete(self._stream_log({
                                "type": "step_complete",
                                "step_number": step_number,
                                "node_name": current_node_name,
                                "state_after": state_after,
                                "message": f"Completed step {step_number}: {current_node_name}"
                            }))
                    except RuntimeError:
                        # No event loop, try creating one
                        try:
                            asyncio.run(self._stream_log({
                                "type": "step_complete",
                                "step_number": step_number,
                                "node_name": current_node_name,
                                "state_after": state_after,
                                "message": f"Completed step {step_number}: {current_node_name}"
                            }))
                        except:
                            pass  # Skip streaming if async not available
                
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
                
                # Stream error if WebSocket connected
                if self.run_id:
                    try:
                        asyncio.run(self._stream_log({
                            "type": "error",
                            "step_number": step_number,
                            "node_name": current_node_name,
                            "error": str(e),
                            "message": f"Error in step {step_number}: {str(e)}"
                        }))
                    except:
                        pass
                
                raise ValueError(f"Error executing node '{current_node_name}': {str(e)}")
        
        # Check if we hit max steps (possible infinite loop)
        if step_number >= self.max_steps:
            raise ValueError(f"Workflow exceeded maximum steps ({self.max_steps}). Possible infinite loop.")
        
        # Stream completion message
        if self.run_id:
            try:
                asyncio.run(self._stream_log({
                    "type": "workflow_complete",
                    "steps_executed": step_number,
                    "final_state": state.to_dict(),
                    "message": f"Workflow completed successfully in {step_number} steps"
                }))
            except:
                pass
        
        return {
            "final_state": state.to_dict(),
            "execution_log": [step.to_dict() for step in self.execution_log],
            "steps_executed": step_number
        }
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get the execution log."""
        return [step.to_dict() for step in self.execution_log]
