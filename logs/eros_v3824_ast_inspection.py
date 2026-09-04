import ast

path = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER\services\eros_frontend_adapter.py"

with open(path, "r", encoding="utf-8-sig") as f:
    source = f.read()

tree = ast.parse(source)

print("AST PARSE : PASS")

for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == "EROSFrontendAdapter":
        print("CLASS : FOUND")

        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "decision_audit":
                print("decision_audit : FOUND")
                print("AST LINE : " + str(item.lineno))
                print("AST END  : " + str(item.end_lineno))
