import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scanner.market_scanner import market_scan

print("SCANNER IMPORT : PASS")

df = market_scan()

print("MARKET SCAN : PASS")
print("TYPE :", type(df).__name__)

try:
    print("ROWS :", len(df))
except Exception:
    print("ROWS : UNKNOWN")

if hasattr(df, "columns"):
    print("COLUMNS :")
    for c in df.columns:
        print(" -", c)

print("READ-ONLY SCAN : PASS")
