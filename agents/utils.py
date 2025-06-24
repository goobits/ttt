"""
Utility functions for Agents.py
"""

import json
from typing import Dict, Any


def format_prompt_with_context(prompt: str, context: Dict[str, Any]) -> str:
    """
    Format a prompt with additional context like code, JSON, images, etc.
    
    Args:
        prompt: The base prompt
        context: Dictionary of additional context
    
    Returns:
        Formatted prompt string
    """
    formatted = prompt
    
    for key, value in context.items():
        if key == "code":
            # Format code blocks
            language = context.get("language", "python")
            formatted += f"\n\n```{language}\n{value}\n```"
            
        elif key == "json":
            # Format JSON data
            if isinstance(value, str):
                formatted += f"\n\n```json\n{value}\n```"
            else:
                formatted += f"\n\n```json\n{json.dumps(value, indent=2)}\n```"
                
        elif key == "text":
            # Plain text addition
            formatted += f"\n\n{value}"
            
        elif key == "url":
            # URL reference
            formatted += f"\n\nURL: {value}"
            
        elif key == "file":
            # File content
            formatted += f"\n\nFile: {context.get('filename', 'unknown')}\n```\n{value}\n```"
            
        # Future: Handle images, documents, etc.
        # elif key == "image":
        #     # This would need special handling based on model capabilities
        #     pass
    
    return formatted