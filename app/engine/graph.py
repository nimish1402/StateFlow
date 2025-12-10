"""
Workflow graph definition and management.

A graph consists of nodes and edges that define the workflow structure.
"""

from typing import Dict, List, Optional, Set, Callable, Any
from app.engine.node import Node, FunctionNode
from app.engine.state import WorkflowState


class WorkflowGraph:
    """
    Represents a workflow graph with nodes and edges.
    
    Supports:
    - Simple edges (A -> B)
    - Conditional edges (A -> B if condition, else C)
    - Loops (A -> B -> A until condition)
    """
    
    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize a workflow graph.
        
        Args:
            name: Name of the graph
            description: Optional description
        """
        self.name = name
        self.description = description or f"Workflow: {name}"
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, List[Dict[str, Any]]] = {}  # from_node -> [edge_definitions]
        self.start_node: Optional[str] = None
    
    def add_node(self, node: Node) -> None:
        """
        Add a node to the graph.
        
        Args:
            node: Node to add
        """
        if node.name in self.nodes:
            raise ValueError(f"Node '{node.name}' already exists in graph")
        self.nodes[node.name] = node
        
        # Set as start node if it's the first node
        if self.start_node is None:
            self.start_node = node.name
    
    def add_edge(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[Callable[[WorkflowState], bool]] = None
    ) -> None:
        """
        Add an edge between two nodes.
        
        Args:
            from_node: Source node name
            to_node: Destination node name
            condition: Optional condition function that takes state and returns bool
        """
        if from_node not in self.nodes:
            raise ValueError(f"Source node '{from_node}' not found in graph")
        if to_node not in self.nodes:
            raise ValueError(f"Destination node '{to_node}' not found in graph")
        
        if from_node not in self.edges:
            self.edges[from_node] = []
        
        self.edges[from_node].append({
            "to": to_node,
            "condition": condition
        })
    
    def set_start_node(self, node_name: str) -> None:
        """
        Set the starting node for the workflow.
        
        Args:
            node_name: Name of the start node
        """
        if node_name not in self.nodes:
            raise ValueError(f"Node '{node_name}' not found in graph")
        self.start_node = node_name
    
    def get_next_node(self, current_node: str, state: WorkflowState) -> Optional[str]:
        """
        Get the next node to execute based on current node and state.
        
        Args:
            current_node: Current node name
            state: Current workflow state
            
        Returns:
            Next node name, or None if no next node (end of workflow)
        """
        if current_node not in self.edges:
            return None
        
        # Check edges in order
        for edge in self.edges[current_node]:
            condition = edge.get("condition")
            
            # If no condition, or condition is True, follow this edge
            if condition is None or condition(state):
                return edge["to"]
        
        # No matching edge found
        return None
    
    def validate(self) -> List[str]:
        """
        Validate the graph structure.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check if graph has nodes
        if not self.nodes:
            errors.append("Graph has no nodes")
            return errors
        
        # Check if start node is set
        if self.start_node is None:
            errors.append("No start node set")
        elif self.start_node not in self.nodes:
            errors.append(f"Start node '{self.start_node}' not found in graph")
        
        # Check for orphaned nodes (nodes with no incoming edges except start)
        nodes_with_incoming = {self.start_node}
        for from_node, edges in self.edges.items():
            for edge in edges:
                nodes_with_incoming.add(edge["to"])
        
        orphaned = set(self.nodes.keys()) - nodes_with_incoming
        if orphaned:
            errors.append(f"Orphaned nodes (no incoming edges): {orphaned}")
        
        # Check for edges referencing non-existent nodes
        for from_node, edges in self.edges.items():
            if from_node not in self.nodes:
                errors.append(f"Edge from non-existent node: {from_node}")
            for edge in edges:
                if edge["to"] not in self.nodes:
                    errors.append(f"Edge to non-existent node: {edge['to']}")
        
        return errors
    
    def get_all_nodes(self) -> List[str]:
        """Get list of all node names."""
        return list(self.nodes.keys())
    
    def __repr__(self) -> str:
        return f"WorkflowGraph(name='{self.name}', nodes={len(self.nodes)}, edges={len(self.edges)})"
