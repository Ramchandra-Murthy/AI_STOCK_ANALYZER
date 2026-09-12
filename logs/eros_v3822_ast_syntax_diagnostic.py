import ast
import sys

path = sys.argv[1]

try:
    source = open(path, encoding="utf-8").read()
    ast.parse(source, filename=path)
    print("AST PARSE : PASS")
except SyntaxError as e:
    print("AST PARSE : FAIL")
    print(f"TYPE      : {type(e).__name__}")
    print(f"LINE      : {e.lineno}")
    print(f"COLUMN    : {e.offset}")
    print(f"TEXT      : {e.text!r}")
    print(f"MESSAGE   : {e.msg}")
    sys.exit(2)
except Exception as e:
    print("AST PARSE : FAIL")
    print(f"TYPE      : {type(e).__name__}")
    print(f"MESSAGE   : {e}")
    sys.exit(3)
