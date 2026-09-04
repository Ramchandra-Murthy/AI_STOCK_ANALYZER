import os
import sys

os.environ["PYTHONPATH"] = os.getcwd()

print("PYTHON :", sys.executable)
print("PROJECT ROOT :", os.getcwd())

from services.eros_frontend_adapter import EROSFrontendAdapter

print("ADAPTER IMPORT : PASS")

adapter = EROSFrontendAdapter()

print("ADAPTER INSTANCE : PASS")

print("")
print("SNAPSHOT TEST")

snapshot = adapter.snapshot()

print("SNAPSHOT : PASS")
print(snapshot)

print("")
print("GOVERNANCE TEST")

governance = adapter.governance()

print("GOVERNANCE : PASS")
print(governance)

print("")
print("DASHBOARD SNAPSHOT TEST")

dashboard = adapter.dashboard_snapshot()

print("DASHBOARD SNAPSHOT : PASS")
print(dashboard)

print("")
print("STOCK ANALYSIS TEST")

result = adapter.stock_analysis("RELIANCE.NS")

print("STOCK ANALYSIS : PASS")
print("TYPE :", type(result).__name__)

print("")
print("MARKET SCAN TEST")

scan = adapter.market_scan()

print("MARKET SCAN : PASS")
print("TYPE :", type(scan).__name__)

if scan is not None:

    print("ROWS :", len(scan))

    print("COLUMNS :")

    for column in scan.columns:
        print(" -", column)

print("")
print("READ-ONLY RUNTIME TEST : PASS")
