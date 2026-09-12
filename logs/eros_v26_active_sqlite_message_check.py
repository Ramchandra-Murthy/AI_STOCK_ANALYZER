import io
import os
import tokenize

root = os.getcwd()

files = []

for base in [
    os.path.join(root, "services"),
    os.path.join(root, "scanner"),
    os.path.join(root, "data"),
]:
    if os.path.isdir(base):
        for dirpath, _, filenames in os.walk(base):
            for filename in filenames:
                if filename.endswith(".py"):
                    files.append(os.path.join(dirpath, filename))

found = []

for path in files:

    with open(path, encoding="utf-8") as f:
        source = f.read()

    tokens = tokenize.generate_tokens(io.StringIO(source).readline)

    for tok in tokens:

        if tok.type == tokenize.STRING:

            value = tok.string.lower()

            if "saved to sqlite successfully" in value:
                found.append(path)

if found:

    print("ACTIVE SQLITE SAVE MESSAGE : FOUND")

    for path in found:
        print(path)

    raise SystemExit(2)

print("ACTIVE SQLITE SAVE MESSAGE : NONE")
