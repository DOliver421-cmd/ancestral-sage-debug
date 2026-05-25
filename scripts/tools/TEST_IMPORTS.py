#!/usr/bin/env python3
"""
Minimal test case: reproduce the import error that happens in Docker

This simulates what happens when the app starts in the Docker container.
We'll try to import modules in the same order server.py does.
"""

import sys
import os

# Simulate Docker PYTHONPATH environment
# PYTHONPATH=/app in Dockerfile
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/backend')

print("=" * 60)
print("TEST: Reproducing server.py imports")
print("=" * 60)
print(f"\nPython path: {sys.path[:3]}")
print(f"Working directory: {os.getcwd()}")
print()

# Try the imports that server.py does
test_imports = [
    ("prompts.ancestral_sage_prompt", None),
    ("prompts.orchestrator", None),
    ("seed", "MODULES"),
    ("seed_labs", "ONLINE_LABS"),
    ("recovery", "generate_recovery_codes"),
    ("revenue_operations_integration", None),
]

passed = 0
failed = 0

for module_name, attr in test_imports:
    try:
        print(f"[TEST] Importing {module_name}...", end=" ")
        module = __import__(module_name, fromlist=[attr] if attr else [])
        if attr:
            getattr(module, attr)
        print("✓ PASS")
        passed += 1
    except Exception as e:
        print(f"✗ FAIL")
        print(f"  Error: {type(e).__name__}: {e}")
        failed += 1
    print()

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    sys.exit(1)
