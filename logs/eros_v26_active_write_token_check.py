import os
import io
import tokenize

ROOT = os.getcwd()

critical = [
    os.path.join(ROOT, "services", "analyzer.py"),
    os.path.join(ROOT, "services", "eros_frontend_adapter.py"),
    os.path.join(ROOT, "scanner", "market_scanner.py"),
    os.path.join(ROOT, "stock_dashboard.py"),
]

patterns = [
    "save_dataframe",
    "to_sql",
    "executemany",
    "commit(",
    "INSERT INTO",
    "UPDATE ",
    "DELETE ",
    "replace into",
]

found = []

for path in critical:

    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except Exception as exc:
        print(f"TOKENIZE ERROR: {path}: {exc}")
        raise

    # Reconstruct only executable tokens.
    executable = []

    for tok in tokens:

        if tok.type in (
            tokenize.COMMENT,
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.ENCODING,
            tokenize.ENDMARKER,
        ):
            continue

        executable.append(tok.string)

    active_text = " ".join(executable)

    for pattern in patterns:

        if pattern in active_text:

            found.append(
                f"{path} : ACTIVE MATCH : {pattern}"
            )

if found:

    print("ACTIVE EXECUTABLE WRITE REFERENCES : FOUND")

    for item in found:
        print(item)

    raise SystemExit(2)

print("ACTIVE EXECUTABLE WRITE REFERENCES : NONE")
