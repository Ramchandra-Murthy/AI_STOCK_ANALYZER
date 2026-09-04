import ast
import sys

path = sys.argv[1]

try:
    source = open(path, "r", encoding="utf-8").read()
    ast.parse(source, filename=path)
    print("AST_PARSE : PASS")
except SyntaxError as e:
    print("AST_PARSE : FAIL")
    print("MESSAGE   :", e.msg)
    print("LINE      :", e.lineno)
    print("COLUMN    :", e.offset)
    print("TEXT      :", repr(e.text))
    sys.exit(2)
except Exception as e:
    print("AST_PARSE : ERROR")
    print(type(e).__name__)
    print(str(e))
    sys.exit(3)