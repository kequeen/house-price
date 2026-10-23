"""Generate offline browser data and projected province paths from retained sources."""
import json
import math
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs' / 'data'

def albers(point):
    lng, lat = point[:2]
    phi1, phi2 = math.radians(25), math.radians(47)
    n = (math.sin(phi1) + math.sin(phi2)) / 2
    c = math.cos(phi1) ** 2 + 2 * n * math.sin(phi1)
    rho = math.sqrt(c - 2 * n * math.sin(math.radians(lat))) / n
    theta = n * math.radians(lng - 105)
    return rho * math.sin(theta), -rho * math.cos(theta)

def main():
    data = json.loads((DATA / 'housing-income-2024.json').read_text())
    assert len(data['records']) == 31 and len({r['code'] for r in data['records']}) == 31
    for r in data['records']:
        assert r['year'] == data['statisticalYear'] == 2024
        assert r['price'] > 0 and r['urbanIncome'] > 0
        assert abs(r['crossCheckDifference']) < 1
    for source in data['sources']:
        source['sha256'] = hashlib.sha256((DATA / source['localFile']).read_bytes()).hexdigest()
    (DATA / 'housing-income-2024.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (DATA / 'housing-data.js').write_text('window.HOUSING_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    geo = json.loads((DATA / 'china-provinces.geojson').read_text())
    main_points = []
    for f in geo['features']:
        if f['properties']['adcode'] == '100000_JD':
            continue
        polygons = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']]
        for poly in polygons:
            for ring in poly:
                main_points.extend(albers(p) for p in ring if p[1] >= 17)
    xs, ys = zip(*main_points)
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    scale = min(690/(maxx-minx), 425/(maxy-miny))
    ox, oy = (750-(maxx-minx)*scale)/2, 15
    def project(p):
        x,y=albers(p)
        return round(ox+(x-minx)*scale,2),round(oy+(y-miny)*scale,2)
    shapes=[]
    inset=[]
    def ring_path(ring, inset_mode=False):
        points=[(round(647+(p[0]-106)*3.8,2),round(438-(p[1]-3)*3.8,2)) if inset_mode else project(p) for p in ring]
        return 'M'+'L'.join(f'{x},{y}' for x,y in points)+'Z'
    records={r['code']:r for r in data['records']}
    for f in geo['features']:
        prop=f['properties']; code=str(prop['adcode'])
        polygons=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
        parts=[]
        for poly in polygons:
            for ring in poly:
                if code=='100000_JD' or max(p[1] for p in ring)<17:
                    inset.append(ring_path(ring,True))
                else:
                    parts.append(ring_path(ring))
        if not parts: continue
        center=prop.get('centroid') or prop.get('center')
        label=project(center) if center else None
        # Small coastal regions get clear labels connected to their geography.
        offsets={'110000':(16,-16),'120000':(26,2),'310000':(30,0),'810000':(28,0),'820000':(-5,18)}
        dx,dy=offsets.get(code,(0,0))
        name=records.get(code,{}).get('name',{'710000':'台湾','810000':'香港','820000':'澳门'}.get(code,prop['name']))
        shapes.append({'code':code,'name':name,'path':''.join(parts),'label':label,'offset':[dx,dy],'available':code in records})
    output={'features':shapes,'inset':''.join(inset),'source':'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json'}
    (DATA / 'map-data.js').write_text('window.PROVINCE_MAP='+json.dumps(output,ensure_ascii=False,separators=(',',':'))+';\n')
    print(f'Prepared {len(data["records"])} official records and {len(shapes)} province shapes.')

if __name__ == '__main__':
    main()
