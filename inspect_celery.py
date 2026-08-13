from pathlib import Path

# Search for celery_app.py or files containing CeleryFacade
for p in Path('.').rglob('*.py'):
    try:
        content = p.read_text(encoding='utf-8-sig')
        if 'CeleryFacade' in content or 'send_task' in content:
            print(f'=== FILE: {p} ===')
            lines = content.splitlines()
            for idx, line in enumerate(lines):
                if 'CeleryFacade' in line or 'send_task' in line:
                    start = max(0, idx - 5)
                    end = min(len(lines), idx + 15)
                    for i in range(start, end):
                        print(f'{i+1:03d}: {lines[i]}')
                    print('-' * 40)
    except Exception:
        pass
