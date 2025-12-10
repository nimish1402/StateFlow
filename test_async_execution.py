"""
Test client for async workflow execution.

This script demonstrates how to run workflows asynchronously and poll for results.
"""

import requests
import time
import json


def run_workflow_async():
    """
    Run workflow asynchronously and poll for completion.
    """
    print("StateFlow Async Execution Test")
    print("=" * 60)
    
    # Step 1: Create a graph
    print("\n1️⃣  Creating workflow graph...")
    graph_response = requests.post("http://localhost:8000/graph/create", json={
        "name": "code_review_async_test",
        "description": "Code review workflow with async execution",
        "nodes": [
            {"name": "extract_functions", "function": "extract_functions"},
            {"name": "check_complexity", "function": "check_complexity"},
            {"name": "detect_issues", "function": "detect_issues"},
            {"name": "suggest_improvements", "function": "suggest_improvements"},
            {"name": "calculate_score", "function": "calculate_quality_score"}
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
    })
    
    if graph_response.status_code != 201:
        print(f"❌ Failed to create graph: {graph_response.text}")
        return
    
    graph_id = graph_response.json()["graph_id"]
    print(f"✅ Graph created: {graph_id}")
    
    # Step 2: Start async execution
    print("\n2️⃣  Starting async workflow execution...")
    
    sample_code = '''
def calculate_sum(a, b):
    return a + b

def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

def analyze_text(text):
    words = text.split()
    return len(words)
'''
    
    # Use the async endpoint
    run_response = requests.post("http://localhost:8000/graph/run/async", json={
        "graph_id": graph_id,
        "initial_state": {
            "code": sample_code,
            "threshold": 70.0,
            "max_iterations": 3,
            "iterations": 0
        }
    })
    
    if run_response.status_code != 200:
        print(f"❌ Failed to start async workflow: {run_response.text}")
        return
    
    result = run_response.json()
    run_id = result["run_id"]
    
    print(f"✅ Async workflow started!")
    print(f"   Run ID: {run_id}")
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")
    
    # Step 3: Poll for completion
    print("\n3️⃣  Polling for completion...")
    print("=" * 60)
    
    poll_count = 0
    max_polls = 30  # Maximum 30 seconds
    
    while poll_count < max_polls:
        poll_count += 1
        
        # Get current state
        state_response = requests.get(f"http://localhost:8000/graph/state/{run_id}")
        
        if state_response.status_code != 200:
            print(f"❌ Failed to get state: {state_response.text}")
            break
        
        state = state_response.json()
        status = state["status"]
        
        # Display progress
        steps_completed = len(state.get("execution_logs", []))
        print(f"Poll {poll_count}: Status={status}, Steps={steps_completed}")
        
        # Check if completed or failed
        if status == "completed":
            print("\n✅ Workflow completed successfully!")
            print("=" * 60)
            
            # Display results
            final_state = state["current_state"]
            print(f"Quality Score: {final_state.get('quality_score', 'N/A')}")
            print(f"Iterations: {final_state.get('iterations', 'N/A')}")
            print(f"Issues Found: {final_state.get('issue_count', 'N/A')}")
            
            if final_state.get('suggestions'):
                print("\nSuggestions:")
                for suggestion in final_state['suggestions']:
                    print(f"  • {suggestion}")
            
            print(f"\nExecution Logs ({len(state['execution_logs'])} steps):")
            for log in state['execution_logs']:
                print(f"  Step {log['step_number']}: {log['node_name']}")
            
            break
            
        elif status == "failed":
            print(f"\n❌ Workflow failed!")
            print(f"Error: {state.get('error_message', 'Unknown error')}")
            break
            
        elif status == "running":
            print(f"   ⏳ Workflow is running... ({steps_completed} steps completed)")
        
        # Wait before next poll
        time.sleep(1)
    
    if poll_count >= max_polls:
        print("\n⚠️  Polling timeout reached")
    
    print("\n" + "=" * 60)
    print("✅ Async execution test completed!")


def check_run_status(run_id: str):
    """
    Check the status of a specific run.
    
    Args:
        run_id: Workflow run ID
    """
    print(f"Checking status for run: {run_id}")
    print("=" * 60)
    
    response = requests.get(f"http://localhost:8000/graph/state/{run_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get state: {response.text}")
        return
    
    state = response.json()
    
    print(f"Status: {state['status']}")
    print(f"Graph ID: {state['graph_id']}")
    print(f"Started: {state.get('started_at', 'N/A')}")
    print(f"Completed: {state.get('completed_at', 'N/A')}")
    print(f"Steps: {len(state.get('execution_logs', []))}")
    
    if state['status'] == 'completed':
        print(f"\nFinal State:")
        print(json.dumps(state['current_state'], indent=2))


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Check specific run status
        run_id = sys.argv[1]
        check_run_status(run_id)
    else:
        # Run full async test
        run_workflow_async()
