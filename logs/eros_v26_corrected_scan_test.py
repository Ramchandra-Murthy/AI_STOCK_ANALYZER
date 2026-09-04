import os
import sys

ROOT = os.getcwd()

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scanner.market_scanner import market_scan

df = market_scan()

if df is None:
    raise RuntimeError("MARKET_SCAN_RETURNED_NONE")

print("MARKET SCAN : PASS")
print("TYPE :", type(df).__name__)

try:
    print("ROWS :", len(df))
except Exception:
    pass

try:
    print("COLUMNS :")
    for column in df.columns:
        print(" -", column)
except Exception:
    pass
