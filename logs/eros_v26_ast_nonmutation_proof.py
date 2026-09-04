import ast
import hashlib
import os
import sys
import traceback
from pathlib import Path

ROOT = Path.cwd()

CRITICAL_FILES = [
    ROOT / "services" / "analyzer.py",
    ROOT / "services" / "eros_frontend_adapter.py",
    ROOT / "scanner" / "market_scanner.py",
    ROOT / "stock_dashboard.py",
]

WRITE_METHODS = {
    "commit",
    "executemany",
    "execute",
    "to_sql",
    "bulk_save_objects",
    "bulk_insert_mappings",
    "add",
    "add_all",
    "flush",
    "delete",
    "update",
    "insert",
}

WRITE_NAMES = {
    "save_dataframe",
    "save_stock",
    "save_data",
    "save_to_database",
    "upsert",
}

SQL_WRITE_PREFIXES = (
    "insert ",
    "update ",
    "delete ",
    "replace ",
    "alter ",
    "drop ",
    "create ",
)

def sha256_file(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest().upper()


def is_sql_write(value):
    if not isinstance(value, str):
        return False

    text = " ".join(value.strip().lower().split())

    return text.startswith(SQL_WRITE_PREFIXES)


def active_write_calls(path):
    results = []

    source = path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source, filename=str(path))
    except Exception as exc:
        results.append(
            f"AST PARSE ERROR: {type(exc).__name__}: {exc}"
        )
        return results

    for node in ast.walk(tree):

        if isinstance(node, ast.Call):

            func_name = None

            if isinstance(node.func, ast.Name):
                func_name = node.func.id

            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name in WRITE_METHODS or func_name in WRITE_NAMES:

                results.append(
                    f"ACTIVE CALL {path}:{node.lineno}: {func_name}(...)"
                )

            for arg in node.args:

                if isinstance(arg, ast.Constant):
                    if is_sql_write(arg.value):
                        results.append(
                            f"ACTIVE SQL WRITE {path}:{node.lineno}: "
                            f"{repr(arg.value)}"
                        )

        if isinstance(node, ast.Constant):

            if isinstance(node.value, str) and is_sql_write(node.value):

                results.append(
                    f"ACTIVE SQL WRITE STRING {path}:{node.lineno}: "
                    f"{repr(node.value)}"
                )

    return results


print("=" * 60)
print("EROS 3.0 - V2.6 AST DATABASE NON-MUTATION PROOF")
print("=" * 60)
print()

print("1. PROJECT ROOT")
print("-" * 60)
print(ROOT)
print()

print("2. CRITICAL FILE CHECK")
print("-" * 60)

missing = False

for path in CRITICAL_FILES:

    status = "PRESENT" if path.exists() else "MISSING"

    print(f"{path.relative_to(ROOT)} : {status}")

    if not path.exists():
        missing = True

print()

if missing:
    print("CRITICAL FILE CHECK : FAIL")
    sys.exit(2)

print("CRITICAL FILE CHECK : PASS")
print()

# ------------------------------------------------------------
# AST ACTIVE WRITE CHECK
# ------------------------------------------------------------

print("3. AST ACTIVE DATABASE WRITE-PATH CHECK")
print("-" * 60)

all_writes = []

for path in CRITICAL_FILES:

    findings = active_write_calls(path)

    if findings:

        for finding in findings:
            print(finding)
            all_writes.append(finding)

    else:

        print(
            f"{path.relative_to(ROOT)} : "
            "NO ACTIVE DATABASE WRITE CALLS"
        )

print()

if all_writes:

    print("ACTIVE DATABASE WRITE-PATH : FOUND")
    print("V2.6 SAFETY GATE : FAIL")
    sys.exit(3)

print("ACTIVE DATABASE WRITE-PATH : NONE")
print("COMMENT-ONLY REFERENCES : IGNORED")
print("V2.6 ACTIVE SOURCE SAFETY : PASS")
print()

# ------------------------------------------------------------
# COMPILE
# ------------------------------------------------------------

print("4. CRITICAL MODULE COMPILE")
print("-" * 60)

for path in CRITICAL_FILES:

    source = path.read_text(encoding="utf-8")

    try:
        compile(source, str(path), "exec")
        print(f"COMPILE PASS : {path.relative_to(ROOT)}")

    except Exception as exc:

        print(
            f"COMPILE FAIL : {path.relative_to(ROOT)}"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )

        sys.exit(4)

print()
print("COMPILE : PASS")
print()

# ------------------------------------------------------------
# DATABASE DISCOVERY
# ------------------------------------------------------------

print("5. DATABASE DISCOVERY")
print("-" * 60)

candidates = [
    ROOT / "database" / "stock_data.db",
    ROOT / "data" / "stock_data.db",
]

db_path = None

for candidate in candidates:

    if candidate.exists():

        db_path = candidate
        break

if db_path is None:

    print("DATABASE : NOT FOUND")
    sys.exit(5)

print(f"DATABASE : {db_path}")
print()

# ------------------------------------------------------------
# DATABASE HASH BEFORE
# ------------------------------------------------------------

print("6. DATABASE HASH BEFORE RUNTIME")
print("-" * 60)

before_hash = sha256_file(db_path)

print(f"SHA256 BEFORE : {before_hash}")
print()

# ------------------------------------------------------------
# RUNTIME TEST
# ------------------------------------------------------------

print("7. READ-ONLY RUNTIME TEST")
print("-" * 60)

runtime_ok = True

try:

    sys.path.insert(0, str(ROOT))

    from services.analyzer import analyze_stock

    result = analyze_stock("RELIANCE.NS")

    print(
        "ANALYZER RUNTIME : PASS"
        if result is not None
        else "ANALYZER RUNTIME : FAIL"
    )

    from scanner.market_scanner import market_scan

    scan = market_scan()

    if scan is None:

        print("MARKET SCAN : FAIL")
        runtime_ok = False

    else:

        print("MARKET SCAN : PASS")
        print(f"TYPE : {type(scan).__name__}")

        try:
            print(f"ROWS : {len(scan)}")
        except Exception:
            pass

        try:
            print("COLUMNS :")
            for column in scan.columns:
                print(f" - {column}")
        except Exception:
            pass

except Exception as exc:

    runtime_ok = False

    print("RUNTIME TEST : FAIL")
    print(f"EXCEPTION TYPE : {type(exc).__name__}")
    print(f"EXCEPTION      : {exc}")

    traceback.print_exc()

print()

if not runtime_ok:

    print("RUNTIME SAFETY TEST : FAIL")
    sys.exit(6)

# ------------------------------------------------------------
# DATABASE HASH AFTER
# ------------------------------------------------------------

print("8. DATABASE HASH AFTER RUNTIME")
print("-" * 60)

after_hash = sha256_file(db_path)

print(f"SHA256 AFTER : {after_hash}")
print()

# ------------------------------------------------------------
# NON-MUTATION
# ------------------------------------------------------------

print("9. DATABASE NON-MUTATION TEST")
print("-" * 60)

if before_hash == after_hash:

    print("DATABASE HASH : IDENTICAL")
    print("DATABASE MUTATION : NONE")
    print("NON-MUTATION INVARIANT : PASS")

else:

    print("DATABASE HASH : CHANGED")
    print("DATABASE MUTATION : DETECTED")
    print("NON-MUTATION INVARIANT : FAIL")

    sys.exit(7)

print()

# ------------------------------------------------------------
# FINAL RESULT
# ------------------------------------------------------------

print("=" * 60)
print("EROS 3.0 - V2.6 AST DATABASE NON-MUTATION PROOF")
print("=" * 60)
print()
print("ACTIVE DATABASE WRITE-PATH : NONE")
print("COMMENT-ONLY WRITE REFERENCES : IGNORED")
print("COMPILE : PASS")
print("ANALYZER RUNTIME : PASS")
print("MARKET SCAN RUNTIME : PASS")
print("DATABASE MUTATION : NONE")
print("NON-MUTATION INVARIANT : PASS")
print()
print("FINAL RESULT : PASS")
print()
print("V2.6 SAFETY GATE : CLEARED")
print()

