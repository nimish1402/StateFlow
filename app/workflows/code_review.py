"""
Code Review Mini-Agent Workflow

This workflow demonstrates all required features:
- Nodes: Multiple processing steps
- State: Shared state flowing through nodes
- Edges: Sequential and conditional routing
- Looping: Repeats until quality threshold is met
"""

from typing import Dict, Any


def create_code_review_workflow() -> Dict[str, Any]:
    """
    Create the code review workflow definition.
    
    This workflow:
    1. Extracts functions from code
    2. Checks complexity
    3. Detects issues
    4. Suggests improvements
    5. Calculates quality score
    6. Loops back if quality is below threshold (max 3 iterations)
    
    Returns:
        Workflow definition dictionary
    """
    workflow = {
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
            {
                "from_node": "extract_functions",
                "to_node": "check_complexity"
            },
            {
                "from_node": "check_complexity",
                "to_node": "detect_issues"
            },
            {
                "from_node": "detect_issues",
                "to_node": "suggest_improvements"
            },
            {
                "from_node": "suggest_improvements",
                "to_node": "calculate_score"
            },
            # Conditional edge: loop if quality is low and haven't exceeded max iterations
            {
                "from_node": "calculate_score",
                "to_node": "detect_issues",
                "condition": "quality_score < threshold and iterations < max_iterations"
            }
            # If condition is false, workflow ends (no more edges)
        ]
    }
    
    return workflow


def get_sample_code() -> str:
    """
    Get sample Python code for testing the workflow.
    
    Returns:
        Sample Python code string
    """
    return '''
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

GLOBAL_CONFIG = {"setting1": "value1", "setting2": "value2"}
GLOBAL_STATE = {}
GLOBAL_CACHE = {}
GLOBAL_DATA = []
'''


def get_initial_state() -> Dict[str, Any]:
    """
    Get initial state for the code review workflow.
    
    Returns:
        Initial state dictionary
    """
    return {
        "code": get_sample_code(),
        "threshold": 70.0,  # Quality score threshold
        "max_iterations": 3,  # Maximum loop iterations
        "iterations": 0  # Current iteration count
    }


# Example usage
if __name__ == "__main__":
    import json
    
    workflow = create_code_review_workflow()
    initial_state = get_initial_state()
    
    print("=== Code Review Workflow Definition ===")
    print(json.dumps(workflow, indent=2))
    
    print("\n=== Initial State ===")
    print(json.dumps(initial_state, indent=2))
