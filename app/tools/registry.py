"""
Tool registry for managing and executing tools.

Tools are Python functions that can be called by workflow nodes.
"""

from typing import Callable, Dict, Any, Optional
from functools import wraps


class ToolRegistry:
    """
    Singleton registry for workflow tools.
    
    Tools are functions that can be registered and called by name.
    """
    
    _instance = None
    _tools: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def register(
        cls,
        name: str,
        function: Callable,
        description: Optional[str] = None
    ) -> None:
        """
        Register a tool.
        
        Args:
            name: Unique name for the tool
            function: Function to register
            description: Optional description of what the tool does
        """
        if name in cls._tools:
            raise ValueError(f"Tool '{name}' is already registered")
        
        cls._tools[name] = {
            "function": function,
            "description": description or function.__doc__ or f"Tool: {name}",
            "name": name
        }
    
    @classmethod
    def get(cls, name: str) -> Callable:
        """
        Get a tool by name.
        
        Args:
            name: Name of the tool
            
        Returns:
            Tool function
            
        Raises:
            KeyError: If tool not found
        """
        if name not in cls._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return cls._tools[name]["function"]
    
    @classmethod
    def get_info(cls, name: str) -> Dict[str, Any]:
        """
        Get tool information.
        
        Args:
            name: Name of the tool
            
        Returns:
            Tool metadata
        """
        if name not in cls._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return cls._tools[name]
    
    @classmethod
    def list_tools(cls) -> Dict[str, str]:
        """
        List all registered tools.
        
        Returns:
            Dictionary of tool names to descriptions
        """
        return {name: info["description"] for name, info in cls._tools.items()}
    
    @classmethod
    def execute(cls, name: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            name: Name of the tool
            state: Current state dictionary
            
        Returns:
            Modified state dictionary
        """
        tool = cls.get(name)
        return tool(state)
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (useful for testing)."""
        cls._tools = {}


def tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator for registering tools.
    
    Usage:
        @tool(name="my_tool", description="Does something")
        def my_tool_function(state: Dict[str, Any]) -> Dict[str, Any]:
            # ... modify state ...
            return state
    
    Args:
        name: Optional name for the tool (defaults to function name)
        description: Optional description
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        ToolRegistry.register(tool_name, func, description)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
