import json
from pathlib import Path
import uuid

base = Path(__file__).resolve().parent / 'app' / 'data' / 'captures'
base.mkdir(parents=True, exist_ok=True)
index = base / 'captures.jsonl'

cid = str(uuid.uuid4())
filename = f'capture-{cid}.jpg'
path = base / filename
with open(path, 'wb') as f:
    f.write(b'TEST-IMAGE-BYTES')

record = {'id': cid, 'filename': filename, 'path': str(path.resolve()), 'metadata': {'timestamp':'2026-07-30T00:00:00Z','distance':'1.23 m','confidence':'99.0%','fps':'30.0'}}
with open(index, 'a', encoding='utf-8') as idx:
    idx.write(json.dumps(record) + '\n')

print('Wrote', path)
print('Index exists', index.exists())
with open(index, 'r', encoding='utf-8') as idx:
    lines = idx.readlines()
    print('Total records', len(lines))
    print('Last record:', lines[-1].strip())
