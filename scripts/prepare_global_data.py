"""Package retained approximate global reference facts for offline browser use."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'docs' / 'data' / 'global'
for source, target, variable in [
    ('global-housing-2026.json', 'global-housing-data.js', 'GLOBAL_HOUSING'),
    ('sea-housing-2026.json', 'sea-housing-data.js', 'SEA_HOUSING'),
]:
    data = json.loads((DATA / source).read_text())
    (DATA / target).write_text(
        'window.' + variable + '=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'Packaged {len(data["records"])} city references for {variable}.')
