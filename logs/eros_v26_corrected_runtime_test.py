import os
import sys

ROOT = os.getcwd()

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.analyzer import analyze_stock

result = analyze_stock("RELIANCE.NS")

if result is None:
    raise RuntimeError("ANALYZER_RETURNED_NONE")

print("ANALYZER RUNTIME : PASS")
print("RESULT TYPE :", type(result).__name__)

if isinstance(result, dict):
    print("RESULT KEYS :", sorted(result.keys()))
