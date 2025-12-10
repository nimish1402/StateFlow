"""
FastAPI routes for workflow graph management and execution.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime

from app.database import get_db
from app.models import (
    Graph,
    WorkflowRun,
    ExecutionLog,
    RunStatus,
    GraphCreate,
    GraphResponse,
    GraphDetail,
    RunRequest,
    RunResponse,
    StateResponse,
    ExecutionLogResponse,
    NodeDefinition,
    EdgeDefinition
)
from app.engine import WorkflowGraph, FunctionNode, WorkflowExecutor
from app.tools.registry import ToolRegistry
from app.api.websocket import manager

router = APIRouter()


@router.websocket("/ws/run/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint for streaming real-time execution logs.
    
    Connect to this endpoint before or during workflow execution
    to receive live updates as each node completes.
    
    Args:
        websocket: WebSocket connection
        run_id: Workflow run ID to stream logs for
        
    Message Format:
        {
            "type": "connected" | "step_complete" | "workflow_complete" | "error",
            "step_number": int,
            "node_name": str,
            "state_after": dict,
            "message": str
        }
    """
    await manager.connect(run_id, websocket)
    try:
        # Keep connection alive and listen for client messages
        while True:
            # Receive text to keep connection open
            # Client can send "ping" to check connection
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(run_id, websocket)


@router.post("/graph/create", response_model=GraphResponse, status_code=201)
def create_graph(graph_data: GraphCreate, db: Session = Depends(get_db)):
    """
    Create a new workflow graph.
    
    Args:
        graph_data: Graph definition with nodes and edges
        db: Database session
        
    Returns:
        Created graph with ID
    """
    # Validate that all referenced functions exist in tool registry
    available_tools = ToolRegistry.list_tools()
    
    for node in graph_data.nodes:
        if node.function not in available_tools:
            raise HTTPException(
                status_code=400,
                detail=f"Function '{node.function}' not found in tool registry. Available tools: {list(available_tools.keys())}"
            )
    
    # Validate edges reference existing nodes
    node_names = {node.name for node in graph_data.nodes}
    for edge in graph_data.edges:
        if edge.from_node not in node_names:
            raise HTTPException(
                status_code=400,
                detail=f"Edge references non-existent source node: {edge.from_node}"
            )
        if edge.to_node not in node_names:
            raise HTTPException(
                status_code=400,
                detail=f"Edge references non-existent destination node: {edge.to_node}"
            )
    
    # Create graph in database
    graph = Graph(
        name=graph_data.name,
        description=graph_data.description,
        nodes=json.dumps([node.model_dump() for node in graph_data.nodes]),
        edges=json.dumps([edge.model_dump() for edge in graph_data.edges])
    )
    
    db.add(graph)
    db.commit()
    db.refresh(graph)
    
    return GraphResponse(
        graph_id=graph.id,
        name=graph.name,
        description=graph.description,
        created_at=graph.created_at
    )


@router.get("/graph/{graph_id}", response_model=GraphDetail)
def get_graph(graph_id: str, db: Session = Depends(get_db)):
    """
    Get graph details by ID.
    
    Args:
        graph_id: Graph ID
        db: Database session
        
    Returns:
        Graph details
    """
    graph = db.query(Graph).filter(Graph.id == graph_id).first()
    
    if not graph:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found")
    
    # Parse nodes and edges
    nodes = [NodeDefinition(**node) for node in json.loads(graph.nodes)]
    edges = [EdgeDefinition(**edge) for edge in json.loads(graph.edges)]
    
    return GraphDetail(
        graph_id=graph.id,
        name=graph.name,
        description=graph.description,
        nodes=nodes,
        edges=edges,
        created_at=graph.created_at,
        updated_at=graph.updated_at
    )


@router.get("/graphs", response_model=List[GraphResponse])
def list_graphs(db: Session = Depends(get_db)):
    """
    List all graphs.
    
    Args:
        db: Database session
        
    Returns:
        List of graphs
    """
    graphs = db.query(Graph).all()
    
    return [
        GraphResponse(
            graph_id=g.id,
            name=g.name,
            description=g.description,
            created_at=g.created_at
        )
        for g in graphs
    ]


def build_workflow_graph(graph: Graph) -> WorkflowGraph:
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
            # Parse condition string into a lambda
            # For now, we'll support simple conditions like "quality_score >= threshold"
            condition_str = edge_data["condition"]
            condition = lambda state, cond=condition_str: eval(cond, {"__builtins__": {}}, state.to_dict())
        
        wf_graph.add_edge(
            from_node=edge_data["from_node"],
            to_node=edge_data["to_node"],
            condition=condition
        )
    
    return wf_graph


@router.post("/graph/run", response_model=RunResponse)
def run_graph(run_request: RunRequest, db: Session = Depends(get_db)):
    """
    Execute a workflow graph.
    
    Args:
        run_request: Run request with graph ID and initial state
        db: Database session
        
    Returns:
        Execution results with final state and logs
    """
    # Get graph
    graph = db.query(Graph).filter(Graph.id == run_request.graph_id).first()
    
    if not graph:
        raise HTTPException(status_code=404, detail=f"Graph '{run_request.graph_id}' not found")
    
    # Create workflow run
    workflow_run = WorkflowRun(
        graph_id=graph.id,
        status=RunStatus.RUNNING,
        current_state=json.dumps(run_request.initial_state)
    )
    db.add(workflow_run)
    db.commit()
    db.refresh(workflow_run)
    
    try:
        # Build workflow graph
        wf_graph = build_workflow_graph(graph)
        
        # Execute workflow with run_id for WebSocket streaming
        executor = WorkflowExecutor(wf_graph, max_steps=100, run_id=workflow_run.id)
        result = executor.execute(run_request.initial_state)
        
        # Update run status
        workflow_run.status = RunStatus.COMPLETED
        workflow_run.current_state = json.dumps(result["final_state"])
        workflow_run.completed_at = db.query(WorkflowRun).filter(
            WorkflowRun.id == workflow_run.id
        ).first().started_at  # Use current time
        
        # Save execution logs
        for log_entry in result["execution_log"]:
            exec_log = ExecutionLog(
                run_id=workflow_run.id,
                node_name=log_entry["node_name"],
                step_number=log_entry["step_number"],
                state_before=json.dumps(log_entry["state_before"]),
                state_after=json.dumps(log_entry["state_after"]),
                error=log_entry.get("error")
            )
            db.add(exec_log)
        
        db.commit()
        db.refresh(workflow_run)
        
        # Get logs
        logs = db.query(ExecutionLog).filter(ExecutionLog.run_id == workflow_run.id).all()
        
        return RunResponse(
            run_id=workflow_run.id,
            graph_id=workflow_run.graph_id,
            status=workflow_run.status,
            final_state=result["final_state"],
            execution_logs=[
                ExecutionLogResponse(
                    node_name=log.node_name,
                    step_number=log.step_number,
                    state_before=json.loads(log.state_before),
                    state_after=json.loads(log.state_after),
                    executed_at=log.executed_at,
                    error=log.error
                )
                for log in logs
            ],
            started_at=workflow_run.started_at,
            completed_at=workflow_run.completed_at,
            error_message=None
        )
        
    except Exception as e:
        # Update run status to failed
        workflow_run.status = RunStatus.FAILED
        workflow_run.error_message = str(e)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.post("/graph/run/async")
async def run_graph_async(
    run_request: RunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Execute a workflow asynchronously in the background.
    
    Returns immediately with run_id. Use GET /graph/state/{run_id}
    to check progress and results.
    
    Args:
        run_request: Run request with graph ID and initial state
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Run ID and pending status
    """
    # Get graph
    graph = db.query(Graph).filter(Graph.id == run_request.graph_id).first()
    
    if not graph:
        raise HTTPException(status_code=404, detail=f"Graph '{run_request.graph_id}' not found")
    
    # Create workflow run with pending status
    workflow_run = WorkflowRun(
        graph_id=graph.id,
        status=RunStatus.PENDING,
        current_state=json.dumps(run_request.initial_state)
    )
    db.add(workflow_run)
    db.commit()
    db.refresh(workflow_run)
    
    # Add to background tasks
    from app.api.background import execute_workflow_background
    background_tasks.add_task(
        execute_workflow_background,
        workflow_run.id,
        run_request.graph_id,
        run_request.initial_state
    )
    
    return {
        "run_id": workflow_run.id,
        "graph_id": workflow_run.graph_id,
        "status": "pending",
        "message": "Workflow execution started in background. Use GET /graph/state/{run_id} to check progress."
    }




@router.get("/graph/state/{run_id}", response_model=StateResponse)
def get_run_state(run_id: str, db: Session = Depends(get_db)):
    """
    Get the current state of a workflow run.
    
    Args:
        run_id: Run ID
        db: Database session
        
    Returns:
        Current state and execution logs
    """
    workflow_run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    
    if not workflow_run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    
    # Get execution logs
    logs = db.query(ExecutionLog).filter(ExecutionLog.run_id == run_id).order_by(ExecutionLog.step_number).all()
    
    return StateResponse(
        run_id=workflow_run.id,
        graph_id=workflow_run.graph_id,
        status=workflow_run.status,
        current_state=json.loads(workflow_run.current_state),
        current_node=workflow_run.current_node,
        execution_logs=[
            ExecutionLogResponse(
                node_name=log.node_name,
                step_number=log.step_number,
                state_before=json.loads(log.state_before),
                state_after=json.loads(log.state_after),
                executed_at=log.executed_at,
                error=log.error
            )
            for log in logs
        ],
        started_at=workflow_run.started_at,
        completed_at=workflow_run.completed_at,
        error_message=workflow_run.error_message
    )


@router.get("/tools")
def list_tools():
    """
    List all available tools in the registry.
    
    Returns:
        Dictionary of tool names to descriptions
    """
    return ToolRegistry.list_tools()
