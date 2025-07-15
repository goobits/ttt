#!/usr/bin/env python3
"""Test various routing scenarios to ensure the fix is robust."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from ai.routing import router

def test_routing_scenarios():
    """Test various routing scenarios."""
    print("=== ROUTING SCENARIOS TEST ===")
    
    # Test 1: No specific backend/model
    print("\n1. No specific backend/model:")
    backend, model = router.smart_route("Hello world")
    print(f"   Backend: {backend.name}, Model: {model}")
    
    # Test 2: Prefer speed
    print("\n2. Prefer speed:")
    backend, model = router.smart_route("Hello world", prefer_speed=True)
    print(f"   Backend: {backend.name}, Model: {model}")
    
    # Test 3: Prefer quality
    print("\n3. Prefer quality:")
    backend, model = router.smart_route("Hello world", prefer_quality=True)
    print(f"   Backend: {backend.name}, Model: {model}")
    
    # Test 4: Explicit cloud backend
    print("\n4. Explicit cloud backend:")
    backend, model = router.smart_route("Hello world", backend="cloud")
    print(f"   Backend: {backend.name}, Model: {model}")
    
    # Test 5: Explicit local backend (should work even if not available)
    print("\n5. Explicit local backend:")
    try:
        backend, model = router.smart_route("Hello world", backend="local")
        print(f"   Backend: {backend.name}, Model: {model}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 6: Explicit cloud model
    print("\n6. Explicit cloud model:")
    backend, model = router.smart_route("Hello world", model="gpt-4")
    print(f"   Backend: {backend.name}, Model: {model}")
    
    # Test 7: Explicit local model
    print("\n7. Explicit local model:")
    backend, model = router.smart_route("Hello world", model="llama2")
    print(f"   Backend: {backend.name}, Model: {model}")

if __name__ == "__main__":
    test_routing_scenarios()