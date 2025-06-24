"""
Chat session management for Agents.py

Handles conversational context and history.
"""

import json
import time
from typing import Dict, List, Optional, Any
from .response import AgentResponse
from .routing import ModelRouter, get_default_router
from .registry import ModelConfiguration, get_default_configuration
from .backends import create_backend
from .utils import format_prompt_with_context


class ChatSession:
    """Manages a conversation with history."""
    
    def __init__(self, model: Optional[str] = None, system: Optional[str] = None,
                 config: Optional[ModelConfiguration] = None):
        """
        Initialize a chat session.
        
        Args:
            model: Specific model to use for the conversation
            system: System prompt to set the assistant's behavior
            config: Model configuration to use
        """
        self.model = model
        self.system = system
        self.history: List[Dict[str, str]] = []
        self.config = config or get_default_configuration()
        self.router = ModelRouter(self.config)
        self.backend = None
        self.model_info = None
        
        # Set up backend if model is specified
        if self.model:
            self._setup_backend()
    
    def _setup_backend(self):
        """Set up the backend for the specified model."""
        self.model_info = self.config.get_model(self.model)
        self.backend = create_backend(self.model_info.provider, self.model_info)
    
    def __call__(self, prompt: str, **kwargs) -> AgentResponse:
        """
        Send a message in the conversation.
        
        Args:
            prompt: The message to send
            **kwargs: Additional context (code=, json=, etc)
        
        Returns:
            AgentResponse with the assistant's reply
        """
        start_time = time.time()
        
        # Add user message to history
        self.history.append({"role": "user", "content": prompt})
        
        # Route to appropriate model if not specified
        if not self.backend:
            self.model_info = self.router.route(prompt, context=self.history)
            self.backend = create_backend(self.model_info.provider, self.model_info)
        
        # Build messages including system prompt and history
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        messages.extend(self.history)
        
        # Handle special context (code=, image=, etc)
        if kwargs:
            formatted_prompt = format_prompt_with_context(prompt, kwargs)
            messages[-1]["content"] = formatted_prompt
        
        try:
            # Get response from backend
            response_text = self.backend.complete(messages)
            
            # Add assistant response to history
            self.history.append({"role": "assistant", "content": response_text})
            
            response = AgentResponse(
                content=response_text,
                model=self.model_info.name,
                time=time.time() - start_time,
                metadata={
                    "provider": self.model_info.provider,
                    "history_length": len(self.history),
                    "session": True
                }
            )
            
            return response
            
        except Exception as e:
            response = AgentResponse(
                content="",
                model=self.model_info.name if self.model_info else "unknown",
                time=time.time() - start_time,
                _error=e
            )
            return response
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    async def async_call(self, prompt: str, **kwargs) -> AgentResponse:
        """
        Async version of __call__.
        
        Args:
            prompt: The message to send
            **kwargs: Additional context
        
        Returns:
            AgentResponse with the assistant's reply
        """
        start_time = time.time()
        
        # Add user message to history
        self.history.append({"role": "user", "content": prompt})
        
        # Route to appropriate model if not specified
        if not self.backend:
            self.model_info = self.router.route(prompt, context=self.history)
            self.backend = create_backend(self.model_info.provider, self.model_info)
        
        # Build messages
        messages = []
        if self.system:
            messages.append({"role": "system", "content": self.system})
        messages.extend(self.history)
        
        # Handle special context
        if kwargs:
            formatted_prompt = format_prompt_with_context(prompt, kwargs)
            messages[-1]["content"] = formatted_prompt
        
        try:
            # Get async response from backend
            response_text = await self.backend.acomplete(messages)
            
            # Add to history
            self.history.append({"role": "assistant", "content": response_text})
            
            response = AgentResponse(
                content=response_text,
                model=self.model_info.name,
                time=time.time() - start_time,
                metadata={
                    "provider": self.model_info.provider,
                    "history_length": len(self.history),
                    "session": True,
                    "async": True
                }
            )
            
            return response
            
        except Exception as e:
            response = AgentResponse(
                content="",
                model=self.model_info.name if self.model_info else "unknown",
                time=time.time() - start_time,
                _error=e
            )
            return response
    
    def clear(self):
        """Clear conversation history."""
        self.history.clear()
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get a copy of the conversation history."""
        return self.history.copy()
    
    def save(self, path: str):
        """
        Save conversation to a file.
        
        Args:
            path: File path to save to
        """
        with open(path, 'w') as f:
            json.dump({
                'system': self.system,
                'model': self.model,
                'history': self.history
            }, f, indent=2)
    
    def load(self, path: str):
        """
        Load conversation from a file.
        
        Args:
            path: File path to load from
        """
        with open(path, 'r') as f:
            data = json.load(f)
            self.system = data.get('system')
            self.model = data.get('model')
            self.history = data.get('history', [])
            
            # Reset backend to use loaded model
            if self.model:
                self._setup_backend()