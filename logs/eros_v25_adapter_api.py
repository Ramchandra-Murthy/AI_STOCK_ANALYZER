import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

print("=" * 60)
print("EROS 3.0 - V2.5 ADAPTER API DIAGNOSTIC")
print("=" * 60)

print()
print("PROJECT ROOT")
print(ROOT)

print()
print("PYTHON PATH")
print(sys.path[0])

print()
print("IMPORT TEST")

from services.eros_frontend_adapter import EROSFrontendAdapter

print("IMPORT : PASS")

adapter = EROSFrontendAdapter()

print("ADAPTER INSTANCE : PASS")
print("CLASS :", type(adapter).__name__)

print()
print("AVAILABLE PUBLIC API")
print("-" * 60)

methods = [name for name in dir(adapter) if not name.startswith("_")]

for name in methods:
    print(name)

print()
print("SNAPSHOT TEST")
print("-" * 60)

snapshot = adapter.snapshot()
print("SNAPSHOT : PASS")
print(snapshot)

print()
print("GOVERNANCE TEST")
print("-" * 60)

governance = adapter.governance()
print("GOVERNANCE : PASS")
print(governance)

print()
print("DASHBOARD API TEST")
print("-" * 60)

if hasattr(adapter, "dashboard"):
    dashboard = adapter.dashboard()
    print("DASHBOARD : PASS")
    print(dashboard)
else:
    print("DASHBOARD : NOT IMPLEMENTED")

print()
print("=" * 60)
print("EROS 3.0 - V2.5 ADAPTER API DIAGNOSTIC COMPLETE")
print("=" * 60)
