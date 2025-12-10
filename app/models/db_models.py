"""
SQLAlchemy database models for storing graphs, workflow runs, and execution logs.
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.database import Base


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class RunStatus(str, enum.Enum):
    """Workflow run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Graph(Base):
    """
    Stores workflow graph definitions.
    
    A graph contains nodes (steps) and edges (transitions between steps).
    """
    __tablename__ = "graphs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    nodes = Column(Text, nullable=False)  # JSON string
    edges = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    runs = relationship("WorkflowRun", back_populates="graph", cascade="all, delete-orphan")


class WorkflowRun(Base):
    """
    Stores individual workflow execution runs.
    
    Each run tracks the current state and execution status.
    """
    __tablename__ = "workflow_runs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    graph_id = Column(String, ForeignKey("graphs.id"), nullable=False)
    status = Column(SQLEnum(RunStatus), default=RunStatus.PENDING, nullable=False)
    current_state = Column(Text, nullable=False)  # JSON string
    current_node = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    graph = relationship("Graph", back_populates="runs")
    logs = relationship("ExecutionLog", back_populates="run", cascade="all, delete-orphan")


class ExecutionLog(Base):
    """
    Stores step-by-step execution logs for workflow runs.
    
    Each log entry represents one node execution.
    """
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("workflow_runs.id"), nullable=False)
    node_name = Column(String, nullable=False)
    step_number = Column(Integer, nullable=False)
    state_before = Column(Text, nullable=False)  # JSON string
    state_after = Column(Text, nullable=False)  # JSON string
    executed_at = Column(DateTime, default=datetime.utcnow)
    error = Column(Text, nullable=True)
    
    # Relationships
    run = relationship("WorkflowRun", back_populates="logs")
