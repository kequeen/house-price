"""Prepare a north-up Equal Earth world basemap from public-domain Natural Earth."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs' / 'data' / 'global'
SOURCE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson'


def project(lon, lat):
    # Equal Earth forward projection; geographic y points north, SVG y points south.
    theta = math.asin(math.sqrt(3) / 2 * math.sin(math.radians(lat)))
    t2 = theta * theta
    t6 = t2 ** 3
    x = math.radians(lon) * math.cos(theta) / (
        math.sqrt(3) / 2 * (1.340264 - 3 * 0.081106 * t2 + t6 * (7 * 0.000893 + 9 * 0.003796 * t2)))
    y = theta * (1.340264 - 0.081106 * t2 + t6 * (0.000893 + 0.003796 * t2))
    return [round(500 + x * 178, 2), round(263 - y * 178, 2)]


def path(points, close=False):
    return 'M' + 'L'.join(','.join(map(str, project(*p[:2]))) for p in points) + ('Z' if close else '')


def main():
    source = DATA / 'raw' / 'world-countries.geojson'
    geo = json.loads(source.read_text())
    features = []
    for f in geo['features']:
        prop = f['properties']
        if prop['ADM0_A3'] == 'ATA':
            continue
        polygons = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']]
        shapes = ''.join(path(ring, True) for polygon in polygons for ring in polygon)
        features.append({'id': prop['ADM0_A3'], 'name': prop.get('NAME_ZH') or prop['NAME'], 'path': shapes})
    graticule = [path([[lon, lat] for lon in range(-180, 181, 3)]) for lat in [-60, -30, 0, 30, 60]]
    graticule += [path([[lon, lat] for lat in range(-75, 85, 3)]) for lon in range(-150, 180, 30)]
    data = {'projection': 'Equal Earth', 'viewBox': [0, 0, 1000, 520], 'source': SOURCE,
            'license': 'https://www.naturalearthdata.com/about/terms-of-use/',
            'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'features': features, 'graticule': ''.join(graticule)}
    (DATA / 'world-map-data.js').write_text('window.WORLD_MAP=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'Prepared {len(features)} basemap shapes in Equal Earth projection.')


if __name__ == '__main__':
    main()
