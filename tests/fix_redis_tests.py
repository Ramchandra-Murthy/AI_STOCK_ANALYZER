from pathlib import Path

files = [
    Path("/app/tests/production/test_block30o_separate_worker.py"),
    Path("/app/tests/production/test_block30p_dedicated_worker.py"),
    Path("/app/tests/production/test_block30r_diagnostic.py"),
]

old = 'BROKER_URL = "redis://127.0.0.1:6379/0"'
new = 'import os\nBROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")'

for p in files:
    s = p.read_text()

    if old in s:
        p.write_text(s.replace(old, new))
        print("UPDATED:", p)
    else:
        print("NOT FOUND:", p)