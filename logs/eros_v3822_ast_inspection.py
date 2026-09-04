import ast
import sys

path = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER\services\eros_frontend_adapter.py"

try:
    source = open(path, "r", encoding="utf-8").read()
    ast.parse(source, filename=path)
    print("AST PARSE : PASS")
    sys.exit(0)
except SyntaxError as e:
    print("AST PARSE : FAIL")
    print("LINE      :", e.lineno)
    print("OFFSET    :", e.offset)
    print("MESSAGE   :", e.msg)
    print("TEXT      :", repr(e.text))
    sys.exit(2)
except Exception as e:
    print("AST ERROR :", type(e).__name__)
    print("MESSAGE   :", str(e))
    sys.exit(3)