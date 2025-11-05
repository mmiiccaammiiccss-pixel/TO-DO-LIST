from pathlib import Path
import json
import sys
import main

p = Path(__file__).parent / 'lists'
p.mkdir(exist_ok=True)

testfile = p / 'autotest.json'
data = {"name": "autotest", "tasks": ["alpha", "beta"]}
try:
    testfile.write_text(json.dumps(data, indent=2), encoding='utf-8')
    loaded = json.loads(testfile.read_text(encoding='utf-8'))
    if loaded.get('name') != data['name'] or loaded.get('tasks') != data['tasks']:
        print('FAILED: content mismatch')
        sys.exit(2)
except Exception as e:
    print('FAILED:', e)
    sys.exit(3)

print('SMOKE TEST OK:', testfile)
