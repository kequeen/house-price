"""Package retained approximate global reference facts for offline browser use."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'docs' / 'data' / 'global'
data = json.loads((DATA / 'global-housing-2026.json').read_text())
(DATA / 'global-housing-data.js').write_text(
    'window.GLOBAL_HOUSING=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(f'Packaged {len(data["records"])} approximate city references.')
