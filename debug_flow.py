#!/usr/bin/env python3
"""Debug script to trace the AI library flow."""

import logging
import sys
import os
from pathlib import Path

# Add the ai directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Set up debug logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

# Import modules directly without going through __init__.py
from ai.config import get_config, model_registry
from ai.routing import Router
from ai.backends.local import LocalBackend
from ai.backends.cloud import CloudBackend

def trace_flow():
    """Trace the complete flow."""
    
    # Step 1: Load configuration
    print("=== STEP 1: Configuration ===")
    config = get_config()
    print(f"Config default_backend: {config.default_backend}")
    print(f"Config default_model: {config.default_model}")
    
    # Step 2: Check model registry
    print("\n=== STEP 2: Model Registry ===")
    print(f"Model registry aliases: {model_registry.aliases}")
    mistral_model = model_registry.get_model("mistral")
    if mistral_model:
        print(f"Mistral model info: {mistral_model}")
    
    # Step 3: Smart routing
    print("\n=== STEP 3: Smart Routing ===")
    prompt = "hello world"
    
    # Create router instance
    router = Router()
    
    # Manually call smart_route to see what happens
    backend_instance, resolved_model = router.smart_route(prompt)
    print(f"Smart routing result - Backend: {backend_instance.name}, Model: {resolved_model}")
    
    # Step 4: Check backend configurations
    print("\n=== STEP 4: Backend Configurations ===")
    if hasattr(backend_instance, 'default_model'):
        print(f"Selected backend default_model: {backend_instance.default_model}")
    
    # Step 5: Check local backend specifically
    print("\n=== STEP 5: Local Backend Check ===")
    if hasattr(router, '_backends') and 'local' in router._backends:
        local_backend = router._backends['local']
        print(f"Local backend default_model: {local_backend.default_model}")
    else:
        try:
            local_backend = LocalBackend(config.model_dump())
            print(f"New local backend default_model: {local_backend.default_model}")
        except Exception as e:
            print(f"Error creating local backend: {e}")

if __name__ == "__main__":
    trace_flow()