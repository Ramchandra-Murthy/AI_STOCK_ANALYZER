import re
from pathlib import Path

root = Path("services")

print("=" * 100)
print("EROS 3.0 - NEXT BLOCK DISCOVERY AFTER BLOCK 97")
print("=" * 100)

matches = []

for path in root.rglob("block*.py"):

    name = path.name.lower()

    m = re.search(r"block(\d+)", name)

    if not m:
        continue

    block_id = int(m.group(1))

    if block_id >= 98:
        matches.append((block_id, path))

matches.sort(key=lambda x: (x[0], str(x[1])))

print()
print("BLOCKS >= 98 FOUND:")
print("-" * 100)

if not matches:
    print("NO BLOCKS >= 98 FOUND")
else:
    for block_id, path in matches:
        print(f"BLOCK {block_id:03d} : {path}")

print()
print("=" * 100)
print("NEXT BLOCK CANDIDATES")
print("=" * 100)

seen = set()

for block_id, path in matches:

    if block_id in seen:
        continue

    seen.add(block_id)

    print()
    print(f"BLOCK {block_id}")
    print(f"PATH  : {path}")

print()
print("=" * 100)
print("DISCOVERY COMPLETE")
print("=" * 100)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 100)
