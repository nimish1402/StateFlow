"""
WebSocket client for testing real-time workflow execution log streaming.

This script demonstrates how to connect to the StateFlow WebSocket endpoint
and receive live updates as a workflow executes.
"""

import asyncio
import websockets
import json
import requests
import sys


async def stream_workflow_logs(run_id: str):
    """
    Connect to WebSocket and stream workflow execution logs.
    
    Args:
        run_id: Workflow run ID to stream logs for
    """
    uri = f"ws://localhost:8000/ws/run/{run_id}"
    
    print(f"Connecting to WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to workflow {run_id}")
            print("=" * 60)
            
            # Receive messages until workflow completes
            while True:
                try:
                    message = await websocket.recv()
                    log = json.loads(message)
                    
                    # Handle different message types
                    if log["type"] == "connected":
                        print(f"📡 {log['message']}")
                    
                    elif log["type"] == "step_complete":
                        print(f"\n✓ Step {log['step_number']}: {log['node_name']}")
                        print(f"  Message: {log['message']}")
                        # Optionally print state (can be verbose)
                        # print(f"  State: {json.dumps(log['state_after'], indent=2)}")
                    
                    elif log["type"] == "workflow_complete":
                        print(f"\n🎉 {log['message']}")
                        print(f"   Total steps: {log['steps_executed']}")
                        print(f"   Final state keys: {list(log['final_state'].keys())}")
                        break
                    
                    elif log["type"] == "error":
                        print(f"\n❌ Error in step {log['step_number']}: {log['node_name']}")
                        print(f"   Error: {log['error']}")
                        break
                    
                    elif log["type"] == "pong":
                        print("🏓 Pong received")
                    
                except websockets.exceptions.ConnectionClosed:
                    print("\n📡 WebSocket connection closed")
                    break
                except json.JSONDecodeError:
                    print(f"⚠️  Received non-JSON message: {message}")
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


async def run_workflow_with_streaming():
    """
    Create and run a workflow while streaming logs via WebSocket.
    """
    print("StateFlow WebSocket Streaming Test")
    print("=" * 60)
    
    # Step 1: Create a graph
    print("\n1️⃣  Creating workflow graph...")
    graph_response = requests.post("http://localhost:8000/graph/create", json={
        "name": "code_review_workflow_ws_test",
        "description": "Code review workflow with WebSocket streaming",
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
    
    # Step 2: Start workflow execution
    print("\n2️⃣  Starting workflow execution...")
    
    sample_code = '''
def calculate_sum(a, b):
    return a + b

def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
'''
    
    run_response = requests.post("http://localhost:8000/graph/run", json={
        "graph_id": graph_id,
        "initial_state": {
            "code": sample_code,
            "threshold": 70.0,
            "max_iterations": 3,
            "iterations": 0
        }
    })
    
    if run_response.status_code != 200:
        print(f"❌ Failed to start workflow: {run_response.text}")
        return
    
    result = run_response.json()
    run_id = result["run_id"]
    
    print(f"✅ Workflow started: {run_id}")
    print(f"   Status: {result['status']}")
    
    # Step 3: Display results
    print("\n3️⃣  Workflow Results:")
    print("=" * 60)
    print(f"Final Status: {result['status']}")
    print(f"Quality Score: {result['final_state'].get('quality_score', 'N/A')}")
    print(f"Iterations: {result['final_state'].get('iterations', 'N/A')}")
    print(f"Issues Found: {result['final_state'].get('issue_count', 'N/A')}")
    
    if result['final_state'].get('suggestions'):
        print("\nSuggestions:")
        for suggestion in result['final_state']['suggestions']:
            print(f"  • {suggestion}")
    
    print("\n" + "=" * 60)
    print("✅ WebSocket streaming test completed!")


async def test_websocket_only(run_id: str):
    """
    Test WebSocket connection for an existing run.
    
    Args:
        run_id: Existing workflow run ID
    """
    print(f"Testing WebSocket for run: {run_id}")
    await stream_workflow_logs(run_id)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with existing run_id
        run_id = sys.argv[1]
        asyncio.run(test_websocket_only(run_id))
    else:
        # Run full test with new workflow
        asyncio.run(run_workflow_with_streaming())
