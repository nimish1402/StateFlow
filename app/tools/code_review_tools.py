"""
Sample tools for code review workflow.

These tools analyze Python code for quality, complexity, and issues.
"""

from typing import Dict, Any, List
import re
from app.tools.registry import tool


@tool(name="extract_functions", description="Extract function definitions from Python code")
def extract_functions(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract function definitions from Python code.
    
    Args:
        state: Must contain 'code' key with Python code string
        
    Returns:
        State with 'functions' key containing list of function info
    """
    code = state.get("code", "")
    
    # Simple regex to find function definitions
    # Format: def function_name(params):
    pattern = r'def\s+(\w+)\s*\([^)]*\):'
    matches = re.finditer(pattern, code)
    
    functions = []
    for match in matches:
        func_name = match.group(1)
        start_pos = match.start()
        
        # Count lines to get line number
        line_num = code[:start_pos].count('\n') + 1
        
        functions.append({
            "name": func_name,
            "line": line_num,
            "start_pos": start_pos
        })
    
    state["functions"] = functions
    state["function_count"] = len(functions)
    
    return state


@tool(name="check_complexity", description="Calculate code complexity metrics")
def check_complexity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate simple complexity metrics for the code.
    
    This is a simplified complexity checker that counts:
    - Lines of code
    - Number of if/else statements
    - Number of loops
    - Number of functions
    
    Args:
        state: Must contain 'code' key
        
    Returns:
        State with 'complexity_scores' key
    """
    code = state.get("code", "")
    functions = state.get("functions", [])
    
    # Count various complexity indicators
    lines = [line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
    loc = len(lines)
    
    # Count control structures
    if_count = len(re.findall(r'\bif\b', code))
    else_count = len(re.findall(r'\belse\b', code))
    for_count = len(re.findall(r'\bfor\b', code))
    while_count = len(re.findall(r'\bwhile\b', code))
    
    # Calculate complexity score (simple heuristic)
    # Base complexity from LOC
    complexity = loc * 0.1
    
    # Add complexity for control structures
    complexity += (if_count + else_count) * 2
    complexity += (for_count + while_count) * 3
    
    # Per-function complexity (simplified)
    function_complexity = {}
    for func in functions:
        # Simplified: assume each function adds base complexity
        function_complexity[func["name"]] = 5 + (loc / max(len(functions), 1)) * 0.5
    
    state["complexity_scores"] = {
        "total_complexity": round(complexity, 2),
        "lines_of_code": loc,
        "control_structures": if_count + else_count + for_count + while_count,
        "function_complexity": function_complexity
    }
    
    return state


@tool(name="detect_issues", description="Detect common code issues and smells")
def detect_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect common code issues and smells.
    
    Checks for:
    - Long functions (> 50 lines)
    - Missing docstrings
    - Too many parameters
    - Global variables
    - Bare except clauses
    
    Args:
        state: Must contain 'code' key
        
    Returns:
        State with 'issues' key containing list of issues
    """
    code = state.get("code", "")
    functions = state.get("functions", [])
    
    issues = []
    
    # Check for bare except clauses
    if re.search(r'except\s*:', code):
        issues.append({
            "type": "bare_except",
            "severity": "medium",
            "message": "Bare except clause found - should catch specific exceptions"
        })
    
    # Check for global variables (simplified)
    global_vars = re.findall(r'^[A-Z_][A-Z0-9_]*\s*=', code, re.MULTILINE)
    if len(global_vars) > 3:
        issues.append({
            "type": "too_many_globals",
            "severity": "low",
            "message": f"Found {len(global_vars)} global variables - consider reducing"
        })
    
    # Check for missing docstrings
    functions_with_docstrings = len(re.findall(r'def\s+\w+\s*\([^)]*\):\s*"""', code))
    if len(functions) > 0 and functions_with_docstrings < len(functions):
        issues.append({
            "type": "missing_docstrings",
            "severity": "low",
            "message": f"{len(functions) - functions_with_docstrings} functions missing docstrings"
        })
    
    # Check for long lines
    long_lines = [i+1 for i, line in enumerate(code.split('\n')) if len(line) > 100]
    if long_lines:
        issues.append({
            "type": "long_lines",
            "severity": "low",
            "message": f"{len(long_lines)} lines exceed 100 characters"
        })
    
    # Check code length
    loc = len([line for line in code.split('\n') if line.strip()])
    if loc > 200:
        issues.append({
            "type": "long_file",
            "severity": "medium",
            "message": f"File has {loc} lines - consider splitting into smaller modules"
        })
    
    state["issues"] = issues
    state["issue_count"] = len(issues)
    
    return state


@tool(name="suggest_improvements", description="Generate improvement suggestions based on detected issues")
def suggest_improvements(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate improvement suggestions based on detected issues.
    
    Args:
        state: Must contain 'issues' and 'complexity_scores'
        
    Returns:
        State with 'suggestions' key
    """
    issues = state.get("issues", [])
    complexity = state.get("complexity_scores", {})
    
    suggestions = []
    
    # Suggestions based on issues
    issue_types = {issue["type"] for issue in issues}
    
    if "bare_except" in issue_types:
        suggestions.append("Replace bare 'except:' with specific exception types (e.g., 'except ValueError:')")
    
    if "missing_docstrings" in issue_types:
        suggestions.append("Add docstrings to all functions describing their purpose, parameters, and return values")
    
    if "long_lines" in issue_types:
        suggestions.append("Break long lines into multiple lines for better readability (PEP 8 recommends max 79 characters)")
    
    if "long_file" in issue_types:
        suggestions.append("Consider splitting this file into smaller, focused modules")
    
    if "too_many_globals" in issue_types:
        suggestions.append("Reduce global variables by encapsulating them in classes or functions")
    
    # Suggestions based on complexity
    total_complexity = complexity.get("total_complexity", 0)
    if total_complexity > 50:
        suggestions.append("High complexity detected - consider refactoring into smaller functions")
    
    loc = complexity.get("lines_of_code", 0)
    if loc > 100:
        suggestions.append("Consider breaking down large functions into smaller, reusable components")
    
    # General suggestions
    if not suggestions:
        suggestions.append("Code looks good! Consider adding type hints for better code documentation")
    
    state["suggestions"] = suggestions
    
    return state


@tool(name="calculate_quality_score", description="Calculate overall code quality score")
def calculate_quality_score(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate overall code quality score (0-100).
    
    Score is based on:
    - Number and severity of issues
    - Code complexity
    - Code length
    
    Args:
        state: Must contain 'issues' and 'complexity_scores'
        
    Returns:
        State with 'quality_score' key
    """
    issues = state.get("issues", [])
    complexity = state.get("complexity_scores", {})
    
    # Start with perfect score
    score = 100.0
    
    # Deduct points for issues
    for issue in issues:
        severity = issue.get("severity", "low")
        if severity == "high":
            score -= 15
        elif severity == "medium":
            score -= 10
        else:  # low
            score -= 5
    
    # Deduct points for high complexity
    total_complexity = complexity.get("total_complexity", 0)
    if total_complexity > 100:
        score -= 20
    elif total_complexity > 50:
        score -= 10
    elif total_complexity > 25:
        score -= 5
    
    # Deduct points for excessive LOC
    loc = complexity.get("lines_of_code", 0)
    if loc > 300:
        score -= 15
    elif loc > 200:
        score -= 10
    elif loc > 100:
        score -= 5
    
    # Ensure score is between 0 and 100
    score = max(0, min(100, score))
    
    state["quality_score"] = round(score, 2)
    
    # Increment iteration counter
    iterations = state.get("iterations", 0)
    state["iterations"] = iterations + 1
    
    return state
