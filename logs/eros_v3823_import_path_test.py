import sys
import os

print("PYTHON EXECUTABLE :", sys.executable)
print("CURRENT DIRECTORY :", os.getcwd())
print("PROJECT ROOT      :", r"D:\Users\User\Desktop\AI_STOCK_ANALYZER")
print("PROJECT IN PATH   :", r"D:\Users\User\Desktop\AI_STOCK_ANALYZER" in sys.path)

from services.eros_frontend_adapter import EROSFrontendAdapter

print("SERVICES IMPORT   : PASS")
print("CLASS             :", EROSFrontendAdapter.__name__)
