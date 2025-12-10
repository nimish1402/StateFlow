"""
Background execution helper for async workflow processing.
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Graph, WorkflowRun, ExecutionLog, RunStatus
from app.engine import WorkflowGraph, FunctionNode, WorkflowExecutor
from app.tools.registry import ToolRegistry


def build_workflow_graph_from_db(graph: Graph) -> WorkflowGraph:
    """
    Build a WorkflowGraph from database graph.
    
    Args:
        graph: Database graph model
        
    Returns:
        WorkflowGraph instance
    """
    # Parse nodes and edges
    nodes_data = json.loads(graph.nodes)
    edges_data = json.loads(graph.edges)
    
    # Create workflow graph
    wf_graph = WorkflowGraph(name=graph.name, description=graph.description)
    
    # Add nodes
    for node_data in nodes_data:
        function = ToolRegistry.get(node_data["function"])
        node = FunctionNode(
            name=node_data["name"],
            function=function,
            description=node_data.get("description")
        )
        wf_graph.add_node(node)
    
    # Add edges
    for edge_data in edges_data:
        condition = None
        if edge_data.get("condition"):
            condition_str = edge_data["condition"]
            condition = lambda state, cond=condition_str: eval(cond, {"__builtins__": {}}, state.to_dict())
        
        wf_graph.add_edge(
            from_node=edge_data["from_node"],
            to_node=edge_data["to_node"],
            condition=condition
        )
    
    return wf_graph


def execute_workflow_background(run_id: str, graph_id: str, initial_state: dict):
    """
    Execute workflow in background.
    
    This function runs in a background task and updates the database
    with execution results.
    
    Args:
        run_id: Workflow run ID
        graph_id: Graph ID
        initial_state: Initial state dictionary
    """
    db = SessionLocal()
    
    try:
        # Get graph and workflow run
        graph = db.query(Graph).filter(Graph.id == graph_id).first()
        workflow_run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        
        if not graph or not workflow_run:
            return
        
        # Update status to running
        workflow_run.status = RunStatus.RUNNING
        db.commit()
        
        # Build and execute workflow
        wf_graph = build_workflow_graph_from_db(graph)
        executor = WorkflowExecutor(wf_graph, max_steps=100, run_id=run_id)
        result = executor.execute(initial_state)
        
        # Update with results
        workflow_run.status = RunStatus.COMPLETED
        workflow_run.current_state = json.dumps(result["final_state"])
        workflow_run.completed_at = datetime.utcnow()
        
        # Save execution logs
        for log_entry in result["execution_log"]:
            exec_log = ExecutionLog(
                run_id=run_id,
                node_name=log_entry["node_name"],
                step_number=log_entry["step_number"],
                state_before=json.dumps(log_entry["state_before"]),
                state_after=json.dumps(log_entry["state_after"]),
                error=log_entry.get("error")
            )
            db.add(exec_log)
        
        db.commit()
        
    except Exception as e:
        # Update status to failed
        workflow_run.status = RunStatus.FAILED
        workflow_run.error_message = str(e)
        workflow_run.completed_at = datetime.utcnow()
        db.commit()
        
    finally:
        db.close()
