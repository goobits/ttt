#!/usr/bin/env python3
"""Debug script to check model registry."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from ai.config import model_registry
from ai.routing import router

def debug_model_registry():
    """Debug what models are in the registry."""
    print("=== MODEL REGISTRY DEBUG ===")
    
    print(f"Available models: {list(model_registry.models.keys())}")
    
    for name, model_info in model_registry.models.items():
        print(f"  {name}: provider={model_info.provider}, quality={model_info.quality}, speed={model_info.speed}")
    
    print(f"\nAliases: {model_registry.aliases}")
    
    # Test model selection by preference
    print("\n=== MODEL SELECTION BY PREFERENCE ===")
    selected_model = router._select_model_by_preference(None, False, False)
    print(f"Selected model (no preference): {selected_model}")
    
    model_info = model_registry.get_model(selected_model)
    if model_info:
        print(f"Selected model provider: {model_info.provider}")
        print(f"Selected model quality: {model_info.quality}")
        print(f"Selected model speed: {model_info.speed}")
    else:
        print("Model not found in registry")

if __name__ == "__main__":
    debug_model_registry()