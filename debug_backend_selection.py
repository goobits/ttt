#!/usr/bin/env python3
"""Debug script to trace backend selection logic."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from ai.config import get_config
from ai.routing import router
from ai.backends import HAS_LOCAL_BACKEND
from ai.backends.cloud import CloudBackend
if HAS_LOCAL_BACKEND:
    from ai.backends.local import LocalBackend
else:
    LocalBackend = None

def debug_backend_selection():
    """Debug what backend is selected."""
    print("=== BACKEND SELECTION DEBUG ===")
    
    # Check configuration
    config = get_config()
    print(f"Config default_backend: {config.default_backend}")
    print(f"Config fallback_order: {config.fallback_order}")
    print(f"HAS_LOCAL_BACKEND: {HAS_LOCAL_BACKEND}")
    
    # Test cloud backend availability
    print("\n=== CLOUD BACKEND ===")
    cloud_backend = CloudBackend()
    print(f"Cloud backend available: {cloud_backend.is_available}")
    print(f"Cloud backend name: {cloud_backend.name}")
    
    # Test local backend availability if available
    if HAS_LOCAL_BACKEND and LocalBackend:
        print("\n=== LOCAL BACKEND ===")
        local_backend = LocalBackend()
        print(f"Local backend available: {local_backend.is_available}")
        print(f"Local backend name: {local_backend.name}")
    else:
        print("\n=== LOCAL BACKEND ===")
        print("Local backend NOT available (module not imported)")
    
    # Test auto-selection
    print("\n=== AUTO-SELECTION ===")
    try:
        selected_backend = router._auto_select_backend()
        print(f"Auto-selected backend: {selected_backend.name}")
    except Exception as e:
        print(f"Auto-selection failed: {e}")
    
    # Test smart routing
    print("\n=== SMART ROUTING ===")
    try:
        backend, model = router.smart_route("Hello world")
        print(f"Smart route selected backend: {backend.name}")
        print(f"Smart route selected model: {model}")
    except Exception as e:
        print(f"Smart routing failed: {e}")

if __name__ == "__main__":
    debug_backend_selection()