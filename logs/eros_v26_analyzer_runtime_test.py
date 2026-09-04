import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.analyzer import analyze_stock

print("IMPORT : PASS")

result = analyze_stock("RELIANCE.NS")

print("ANALYZER : PASS")
print("RESULT TYPE :", type(result).__name__)

if isinstance(result, dict):
    print("RESULT KEYS :", sorted(result.keys()))

print("RUNTIME TEST : PASS")
