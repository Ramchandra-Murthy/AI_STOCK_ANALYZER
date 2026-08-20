from pprint import pprint
from services.quantitative.block102_frontend_contract import EROSBlock102FrontendContract

print("=" * 70)
print("EROS 3.0 - BLOCK 102 ACTUAL OUTPUT STRUCTURE")
print("=" * 70)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO COMMIT")
print("NO PUSH")
print()

b102 = EROSBlock102FrontendContract()

print("CLASS:")
print(type(b102))
print()

print("BUILDING ACTUAL BLOCK 102 OUTPUT...")
print("-" * 70)

result = b102.build()

print("RESULT TYPE:")
print(type(result))
print()

print("TOP-LEVEL KEYS:")
if isinstance(result, dict):
    for key in result.keys():
        print(f"  {key!r} -> {type(result[key]).__name__}")
else:
    print("RESULT IS NOT A DICT")

print()
print("TOP-LEVEL VALUES:")
print("-" * 70)

if isinstance(result, dict):
    for key, value in result.items():
        if isinstance(value, (dict, list, tuple)):
            print(f"{key!r}:")
            pprint(value, width=120, depth=4)
        else:
            print(f"{key!r}: {value!r}")
        print()

print("=" * 70)
print("BLOCK 102 STRUCTURE DIAGNOSTIC COMPLETE")
print("=" * 70)
