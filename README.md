# StateFlow - Minimal Workflow Engine

A production-ready workflow engine for building agent workflows, similar to LangGraph. StateFlow allows you to define sequences of steps (nodes), connect them with edges, maintain shared state, and execute workflows with support for conditional branching and looping.

## Features

✅ **Node-based Workflow System**
- Define workflow steps as Python functions
- Automatic state management between nodes
- Clean abstraction for reusable components

✅ **Flexible Routing**
- Simple sequential edges (A → B)
- Conditional branching (if condition, go to B, else C)
- Loop support with iteration limits

✅ **Tool Registry**
- Decorator-based tool registration
- Centralized tool management
- Easy tool discovery and execution

✅ **RESTful API**
- Create and manage workflow graphs
- Execute workflows with initial state
- Query execution status and results
- Full OpenAPI documentation

✅ **Execution Logging**
- Step-by-step execution tracking
- State snapshots before/after each node
- Error handling and reporting

✅ **Production Ready**
- SQLite database for persistence
- Pydantic validation
- Comprehensive error handling
- Clean, modular architecture

## Project Structure

```
StateFlow/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database setup
│   │
│   ├── models/              # Data models
│   │   ├── db_models.py     # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas
│   │
│   ├── engine/              # Workflow engine
│   │   ├── state.py         # State management
│   │   ├── node.py          # Node abstraction
│   │   ├── graph.py         # Graph structure
│   │   └── executor.py      # Execution engine
│   │
│   ├── tools/               # Tool system
│   │   ├── registry.py      # Tool registry
│   │   └── code_review_tools.py  # Sample tools
│   │
│   ├── api/                 # API routes
│   │   └── routes.py        # Endpoint definitions
│   │
│   └── workflows/           # Sample workflows
│       └── code_review.py   # Code review workflow
│
├── tests/                   # Test files
├── requirements.txt         # Dependencies
├── run.py                   # Development server
└── test_api_examples.py     # API usage examples
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd StateFlow
```

2. **Create virtual environment**
```bash
python -m venv venv
```

3. **Activate virtual environment**
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Run the server**
```bash
python run.py
```

The API will be available at `http://localhost:8000`

## Quick Start

### 1. Start the Server
```bash
python run.py
```

### 2. Access API Documentation
Open your browser and navigate to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Run the Sample Workflow
```bash
python test_api_examples.py
```

This will:
- Create a code review workflow graph
- Execute it with sample Python code
- Display quality analysis results

## API Endpoints

### Health Check
```http
GET /health
```

### List Available Tools
```http
GET /tools
```

### Create a Workflow Graph
```http
POST /graph/create
Content-Type: application/json

{
  "name": "my_workflow",
  "description": "My workflow description",
  "nodes": [
    {
      "name": "step1",
      "function": "tool_name",
      "description": "First step"
    }
  ],
  "edges": [
    {
      "from_node": "step1",
      "to_node": "step2"
    }
  ]
}
```

### Execute a Workflow
```http
POST /graph/run
Content-Type: application/json

{
  "graph_id": "your-graph-id",
  "initial_state": {
    "key": "value"
  }
}
```

### Get Workflow Execution State
```http
GET /graph/state/{run_id}
```

### Get Graph Details
```http
GET /graph/{graph_id}
```

### List All Graphs
```http
GET /graphs
```

## Sample Workflow: Code Review Mini-Agent

The included code review workflow demonstrates all key features:

### Workflow Steps
1. **Extract Functions** - Parse Python code and extract function definitions
2. **Check Complexity** - Calculate cyclomatic complexity and LOC metrics
3. **Detect Issues** - Identify code smells (bare except, missing docstrings, etc.)
4. **Suggest Improvements** - Generate actionable improvement suggestions
5. **Calculate Quality Score** - Compute overall quality score (0-100)

### Conditional Looping
The workflow loops back to step 3 if:
- Quality score < threshold (default: 70)
- Iterations < max_iterations (default: 3)

### Example Usage

```python
import requests

# Create the workflow
response = requests.post("http://localhost:8000/graph/create", json={
    "name": "code_review_workflow",
    "nodes": [...],  # See test_api_examples.py
    "edges": [...]
})
graph_id = response.json()["graph_id"]

# Run the workflow
response = requests.post("http://localhost:8000/graph/run", json={
    "graph_id": graph_id,
    "initial_state": {
        "code": "def example(): pass",
        "threshold": 70.0,
        "max_iterations": 3,
        "iterations": 0
    }
})

result = response.json()
print(f"Quality Score: {result['final_state']['quality_score']}")
print(f"Suggestions: {result['final_state']['suggestions']}")
```

## What the Engine Supports

### ✅ Implemented Features

1. **Nodes**
   - Function-based nodes
   - Custom node classes via inheritance
   - Automatic state passing

2. **State Management**
   - Dictionary-based state
   - Pydantic validation
   - State history tracking
   - JSON serialization

3. **Edges**
   - Simple sequential edges
   - Conditional routing with Python expressions
   - Multiple outgoing edges per node

4. **Branching**
   - Condition-based routing
   - Multiple paths from single node
   - Dynamic path selection

5. **Looping**
   - Conditional loops
   - Iteration counting
   - Max iteration limits to prevent infinite loops

6. **Tool System**
   - Decorator-based registration
   - Centralized registry
   - Tool discovery API

7. **Execution**
   - Step-by-step execution
   - Comprehensive logging
   - Error handling
   - State persistence

8. **API**
   - RESTful endpoints
   - OpenAPI documentation
   - Request/response validation
   - Error responses

## Architecture Decisions

### Why SQLite?
- Zero configuration
- Portable (single file)
- Perfect for development and small deployments
- Easy to upgrade to PostgreSQL for production

### Why Pydantic?
- Automatic validation
- Clear error messages
- Type safety
- JSON serialization

### Why FastAPI?
- Automatic OpenAPI docs
- High performance
- Modern Python features
- Easy to test

## Future Improvements

Given more time, here are enhancements I would add:

### 1. **Advanced Features**
- [ ] Parallel node execution (fan-out/fan-in)
- [ ] Sub-workflows (nested graphs)
- [ ] Dynamic node creation at runtime
- [ ] Workflow versioning

### 2. **Async Support**
- [ ] Async node execution
- [ ] Background task processing with Celery
- [ ] WebSocket streaming for real-time logs
- [ ] Progress callbacks

### 3. **Enhanced Tooling**
- [ ] CLI for workflow management
- [ ] Visual workflow builder UI
- [ ] Workflow templates library
- [ ] Tool marketplace

### 4. **Production Features**
- [ ] PostgreSQL support
- [ ] Redis caching
- [ ] Metrics and monitoring (Prometheus)
- [ ] Distributed execution
- [ ] Workflow scheduling (cron-like)

### 5. **Developer Experience**
- [ ] More comprehensive test suite
- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] Docker containerization
- [ ] Kubernetes deployment configs

### 6. **Advanced Routing**
- [ ] Map-reduce patterns
- [ ] Conditional parallel execution
- [ ] Dynamic edge creation
- [ ] Workflow composition

### 7. **State Management**
- [ ] State checkpointing
- [ ] State rollback
- [ ] State versioning
- [ ] Partial state updates

### 8. **Observability**
- [ ] Structured logging
- [ ] Distributed tracing
- [ ] Performance profiling
- [ ] Execution analytics

## Testing

### Run All Tests
```bash
pytest tests/
```

### Run API Examples
```bash
python test_api_examples.py
```

### Manual Testing
1. Start the server: `python run.py`
2. Open Swagger UI: `http://localhost:8000/docs`
3. Try the endpoints interactively

## Development

### Adding a New Tool

```python
from app.tools.registry import tool

@tool(name="my_tool", description="Does something useful")
def my_tool(state: dict) -> dict:
    # Process state
    state["result"] = "processed"
    return state
```

### Creating a Custom Node

```python
from app.engine.node import Node
from app.engine.state import WorkflowState

class CustomNode(Node):
    def execute(self, state: WorkflowState) -> WorkflowState:
        # Custom logic
        state.set("custom_key", "custom_value")
        return state
```

### Building a Workflow Programmatically

```python
from app.engine import WorkflowGraph, FunctionNode
from app.tools.registry import ToolRegistry

# Create graph
graph = WorkflowGraph("my_workflow")

# Add nodes
node1 = FunctionNode("step1", ToolRegistry.get("tool1"))
node2 = FunctionNode("step2", ToolRegistry.get("tool2"))

graph.add_node(node1)
graph.add_node(node2)

# Add edges
graph.add_edge("step1", "step2")

# Execute
from app.engine import WorkflowExecutor
executor = WorkflowExecutor(graph)
result = executor.execute({"initial": "state"})
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - feel free to use this project for learning or production.

## Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with ❤️ for the AI Engineering Internship Assignment**
