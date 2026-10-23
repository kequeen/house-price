"""Check local assets, anchors, DOM IDs, math data and map geometry without a browser."""
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'docs'

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
        self.links=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if attrs.get('id'):self.ids.append(attrs['id'])
        for name in ('src','href'):
            if attrs.get(name):self.links.append(attrs[name])

page=Page()
page.feed((WEB / 'index.html').read_text())
assert len(page.ids)==len(set(page.ids)), Counter(page.ids)
for link in page.links:
    parsed=urlsplit(link)
    if parsed.scheme or parsed.netloc:continue
    if not parsed.path:
        if parsed.fragment:assert unquote(parsed.fragment) in page.ids, link
    else:assert (WEB / unquote(parsed.path)).is_file(), link
app=(WEB / 'app.js').read_text()
for identifier in re.findall(r"\$\('([^']+)'\)",app):assert identifier in page.ids, identifier
data=json.loads((WEB / 'data/housing-income-2024.json').read_text())
assert len(data['records'])==31
assert data['national']['price']==10419 and data['national']['urbanIncome']==54188
map_text=(WEB / 'data/map-data.js').read_text()
geo=json.loads(map_text.removeprefix('window.PROVINCE_MAP=').rstrip(';\n'))
assert len(geo['features'])==34
assert sum(f['available'] for f in geo['features'])==31
for feature in geo['features']:
    points=[(float(x),float(y)) for x,y in re.findall(r'(-?[\d.]+),(-?[\d.]+)',feature['path'])]
    assert points, feature['name']
    assert all(0<=x<=750 and 0<=y<=460 for x,y in points), feature['name']
print(f'Static checks passed: {len(page.ids)} unique IDs, {len(page.links)} links/assets, 34 map regions, 31 official records.')
