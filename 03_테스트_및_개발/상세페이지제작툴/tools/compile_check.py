"""compile_check.py

Walk workspace, compile each .py file to check syntax (no import/exec).
Prints a per-file result and a summary.
"""
import sys
from pathlib import Path
import traceback

root = Path.cwd()
exclude_parts = {".venv", "venv", "__pycache__"}

results = []
count_ok = 0
count_err = 0

for p in sorted(root.rglob("*.py")):
    if any(part in exclude_parts for part in p.parts):
        continue
    try:
        src = p.read_text(encoding="utf-8")
        compile(src, str(p), "exec")
        results.append((str(p), True, ""))
        count_ok += 1
    except Exception as e:
        tb = traceback.format_exc()
        results.append((str(p), False, tb))
        count_err += 1

# Print detailed results
print("Code compile check report")
print("Workspace:", root)
print("Total files checked:", count_ok + count_err)
print()
for path, ok, tb in results:
    print("----")
    print(path)
    print("OK" if ok else "ERROR")
    if not ok:
        print(tb)

# Summary
print()
print("SUMMARY:")
print(f"  OK: {count_ok}")
print(f"  ERRORS: {count_err}")

# Exit with code 1 if any error (but caller can ignore)
sys.exit(1 if count_err else 0)
