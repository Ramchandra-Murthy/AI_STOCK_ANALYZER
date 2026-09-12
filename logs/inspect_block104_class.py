import inspect

import services.quantitative.block104_eros_command_center as m

print("=" * 70)
print("BLOCK 104 ACTUAL CLASS INSPECTION")
print("=" * 70)

print("MODULE:", m.__name__)

print("\nPUBLIC CLASSES:")
for name, obj in inspect.getmembers(m, inspect.isclass):
    if obj.__module__ == m.__name__:
        print("CLASS:", name)

print("\nPUBLIC VALUES:")
for name in dir(m):
    if name.isupper():
        try:
            print(name, "=", getattr(m, name))
        except Exception:
            pass
