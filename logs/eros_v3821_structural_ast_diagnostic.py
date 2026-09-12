import ast
import sys

path = sys.argv[1]

try:
    source = open(path, encoding="utf-8").read()
    tree = ast.parse(source, filename=path)

    print("AST_PARSE : PASS")

    methods = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name == "EROSFrontendAdapter":
                print("CLASS : FOUND")

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append((item.name, item.lineno, item.end_lineno))

                for name, start, end in methods:
                    if name == "decision_audit":
                        print("decision_audit : FOUND")
                        print(f"decision_audit START : {start}")
                        print(f"decision_audit END   : {end}")

except SyntaxError as e:
    print("AST_PARSE : FAIL")
    print(f"SYNTAX_ERROR : {e.msg}")
    print(f"LINE         : {e.lineno}")
    print(f"COLUMN       : {e.offset}")
    print(f"TEXT         : {e.text!r}")

    sys.exit(2)

except Exception as e:
    print("AST_PARSE : ERROR")
    print(type(e).__name__)
    print(str(e))
    sys.exit(3)
