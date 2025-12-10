"""
Sample API requests for testing the StateFlow workflow engine.

Run the server first: python run.py
Then use these examples to test the API.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint."""
    print("=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_list_tools():
    """List available tools."""
    print("=== Listing Available Tools ===")
    response = requests.get(f"{BASE_URL}/tools")
    print(f"Status: {response.status_code}")
    print(f"Tools: {json.dumps(response.json(), indent=2)}\n")


def create_code_review_graph():
    """Create the code review workflow graph."""
    print("=== Creating Code Review Graph ===")
    
    graph_data = {
        "name": "code_review_workflow",
        "description": "A workflow for reviewing code quality with iterative improvements",
        "nodes": [
            {
                "name": "extract_functions",
                "function": "extract_functions",
                "description": "Extract function definitions from Python code"
            },
            {
                "name": "check_complexity",
                "function": "check_complexity",
                "description": "Calculate code complexity metrics"
            },
            {
                "name": "detect_issues",
                "function": "detect_issues",
                "description": "Detect common code issues and smells"
            },
            {
                "name": "suggest_improvements",
                "function": "suggest_improvements",
                "description": "Generate improvement suggestions"
            },
            {
                "name": "calculate_score",
                "function": "calculate_quality_score",
                "description": "Calculate overall quality score"
            }
        ],
        "edges": [
            {"from_node": "extract_functions", "to_node": "check_complexity"},
            {"from_node": "check_complexity", "to_node": "detect_issues"},
            {"from_node": "detect_issues", "to_node": "suggest_improvements"},
            {"from_node": "suggest_improvements", "to_node": "calculate_score"},
            {
                "from_node": "calculate_score",
                "to_node": "detect_issues",
                "condition": "quality_score < threshold and iterations < max_iterations"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/graph/create", json=graph_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    if response.status_code == 201:
        return response.json()["graph_id"]
    return None


def run_workflow(graph_id):
    """Run the code review workflow."""
    print(f"=== Running Workflow (Graph ID: {graph_id}) ===")
    
    sample_code = '''
def calculate_sum(a, b):
    return a + b

def process_data(data):
    result = []
    for item in data:
        if item > 0:
            if item % 2 == 0:
                result.append(item * 2)
            else:
                result.append(item * 3)
        else:
            result.append(0)
    return result

def complex_function(x, y, z, a, b, c, d, e, f):
    try:
        value = 0
        for i in range(x):
            for j in range(y):
                if i > j:
                    value += i * j
                else:
                    value -= i * j
        return value
    except:
        return None

GLOBAL_CONFIG = {"setting1": "value1"}
GLOBAL_STATE = {}
GLOBAL_CACHE = {}
GLOBAL_DATA = []
'''
    
    run_data = {
        "graph_id": graph_id,
        "initial_state": {
            "code": sample_code,
            "threshold": 70.0,
            "max_iterations": 3,
            "iterations": 0
        }
    }
    
    response = requests.post(f"{BASE_URL}/graph/run", json=run_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n=== Execution Results ===")
        print(f"Run ID: {result['run_id']}")
        print(f"Status: {result['status']}")
        print(f"\nFinal State:")
        print(f"  Quality Score: {result['final_state'].get('quality_score', 'N/A')}")
        print(f"  Iterations: {result['final_state'].get('iterations', 'N/A')}")
        print(f"  Issues Found: {result['final_state'].get('issue_count', 'N/A')}")
        print(f"\nSuggestions:")
        for suggestion in result['final_state'].get('suggestions', []):
            print(f"  - {suggestion}")
        
        print(f"\n=== Execution Log ({len(result['execution_logs'])} steps) ===")
        for log in result['execution_logs']:
            print(f"  Step {log['step_number']}: {log['node_name']}")
        
        return result['run_id']
    else:
        print(f"Error: {response.text}")
        return None


def get_run_state(run_id):
    """Get the state of a workflow run."""
    print(f"\n=== Getting Run State (Run ID: {run_id}) ===")
    
    response = requests.get(f"{BASE_URL}/graph/state/{run_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Quality Score: {result['current_state'].get('quality_score', 'N/A')}")
        print(f"Steps Executed: {len(result['execution_logs'])}")


if __name__ == "__main__":
    print("StateFlow API Test Suite\n")
    print("Make sure the server is running: python run.py\n")
    print("=" * 60)
    
    # Test health check
    test_health_check()
    
    # List available tools
    test_list_tools()
    
    # Create graph
    graph_id = create_code_review_graph()
    
    if graph_id:
        # Run workflow
        run_id = run_workflow(graph_id)
        
        if run_id:
            # Get run state
            get_run_state(run_id)
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
