"""Collect registered public city statistics; retain raw evidence and reject changed reviewed snapshots.

Python dependencies: requests, beautifulsoup4, lxml (already in backend/requirements.txt).
No login, CAPTCHA solving, individual contracts, scheduled jobs or inferred missing prices.
"""
import argparse
import hashlib
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.collectors.housing import parse_beijing, parse_shijiazhuang


def compact(text):
    return re.sub(r'\s+', '', text)


def rows(html):
    soup = BeautifulSoup(html, 'lxml')
    return [[compact(cell.get_text()) for cell in row.find_all(['td', 'th'], recursive=False)]
            for row in soup.find_all('tr')]


def normalized_record(record, source):
    r = dict(record)
    r['sourceId'] = source['id']
    r['sourceUrl'] = source['url']
    r.setdefault('district', None)
    r.setdefault('count', None)
    r.setdefault('areaSqm', None)
    r.setdefault('amountCny', None)
    r['priceCnyPerSqm'] = (r['amountCny'] / r['areaSqm']
                           if r['houseType'] == 'new-residential' and r['amountCny'] is not None and r['areaSqm'] else None)
    r['units'] = {'count': '套', 'areaSqm': '平方米', 'amountCny': '元', 'priceCnyPerSqm': '元/平方米'}
    for key in ['count', 'areaSqm', 'amountCny']:
        value = r[key]
        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
            raise ValueError(f'Invalid nonnegative numeric field {key}')
    return r


def parse_source(source, body):
    parser = source['parser']
    if parser in ['reviewed-snapshot', 'reviewed-evidence']:
        if hashlib.sha256(body).hexdigest() != source['reviewedSha256']:
            raise ValueError('官方原文已变化，需要重新核对已审阅字段；保留上一版，不自动套用旧数值')
        return source.get('reviewedRecords', []), source.get('reviewedIncomes', [])
    html = body.decode('utf-8-sig')
    if parser == 'wuhan-monthly':
        text = compact(BeautifulSoup(html, 'lxml').get_text())
        match = re.search(r'(\d{4})年(\d{1,2})月新建商品房成交统计情况', text)
        if not match or f'{match[1]}-{int(match[2]):02d}' != source['period'] or '商品住房' not in text:
            raise ValueError('武汉月份或住宅表头与请求不匹配')
        result = []
        for cells in rows(html):
            if len(cells) != 11:
                continue
            try:
                count = float(cells[1].replace(',', ''))
                area = float(cells[2].replace(',', ''))
            except ValueError:
                continue
            if not count.is_integer():
                raise ValueError('住宅套数不是整数')
            district = None if cells[0] == '合计' else cells[0]
            result.append({'id': 'wuhan-' + source['period'].replace('-', '') + '-' + str(len(result)),
                           'city': '武汉', 'cityCode': '420100', 'district': district,
                           'period': source['period'], 'frequency': 'monthly', 'houseType': 'new-residential',
                           'scope': district or '全市（原表统计范围）', 'count': int(count), 'areaSqm': area,
                           'method': 'parsed-official-residential-table',
                           'qualityNote': '仅取商品住房列。原表统计范围包括网上签约和部分合同备案注销后的综合统计数据；分区含开发区等统计分组。未公开金额，不计算均价。'})
        totals = [r for r in result if not r['district']]
        districts = [r for r in result if r['district']]
        if len(totals) != 1 or not districts:
            raise ValueError('缺少唯一合计或分区住宅行')
        for key, tolerance in [('count', 0), ('areaSqm', .15)]:
            if abs(sum(r[key] for r in districts) - totals[0][key]) > tolerance:
                raise ValueError('武汉分区住宅与合计不一致')
        return result, []
    if parser in ['beijing', 'shijiazhuang']:
        parsed = parse_beijing(html) if parser == 'beijing' else parse_shijiazhuang(html, source['period'])
        result = []
        for item in parsed['records']:
            if item['period'] < '2023':
                continue
            r = {'id': f"{source['id']}-{item['period']}-{item['house_type']}", 'city': item['city'],
                 'cityCode': source['cityCode'], 'period': item['period'],
                 'frequency': 'annual' if item['frequency'] == 'year' else 'monthly',
                 'houseType': 'new-residential' if item['house_type'] == 'new' else 'second-hand-residential',
                 'scope': item['scope'], 'count': item['transaction_count'], 'areaSqm': item['area_sqm'],
                 'qualityNote': item['note'], 'method': 'parsed-official-table'}
            result.append(r)
            if parser == 'shijiazhuang':
                for cells in rows(html):
                    if len(cells) != 7 or cells[0] in ['合计', '区域', '区县']:
                        continue
                    try:
                        values = [float(cell.replace(',', '')) for cell in cells[1:]]
                    except ValueError:
                        continue
                    column = 2 if item['house_type'] == 'new' else 4
                    result.append({**r, 'id': r['id'] + '-' + cells[0], 'district': cells[0],
                                   'scope': cells[0], 'count': values[column], 'areaSqm': values[column + 1]})
        return result, []
    if parser == 'shanghai-sales':
        table = rows(html)
        header = next(row for row in table if row and row[0] == '指标' and '2024' in row)
        index = header.index('2024')
        section, values = None, {}
        for row in table:
            if not row:
                continue
            if row[0].startswith('商品房销售面积'):
                section = 'area'
            elif row[0].startswith('商品房销售额'):
                section = 'amount'
            elif row[0].startswith('商品房出租面积'):
                section = None
            elif row[0] == '住宅' and section:
                values[section] = float(row[index].replace(',', ''))
        if set(values) != {'area', 'amount'}:
            raise ValueError('未找到2024住宅销售面积和金额的对应列')
        return [{'id': 'shanghai-sales-2024', 'city': '上海', 'cityCode': '310000', 'period': '2024',
                 'frequency': 'annual', 'houseType': 'new-residential', 'scope': '全市房地产开发企业住宅销售',
                 'areaSqm': round(values['area'] * 10000, 2), 'amountCny': round(values['amount'] * 100000000, 2),
                 'sourceText': f"2024年住宅销售面积{values['area']}万平方米，住宅销售额{values['amount']}亿元。",
                 'qualityNote': '统计年鉴销售口径，不等同网签或二手住宅。', 'method': 'parsed-official-table'}], []
    if parser == 'shanghai-income':
        table = rows(html)
        header = next(row for row in table if row and row[0] == '指标' and '2024' in row)
        index = header.index('2024')
        row = next(row for row in table if row and row[0] == '人均可支配收入')
        value = float(row[index])
        return [], [{'city': '上海', 'year': 2024, 'urbanDisposableIncomeCnyPerYear': value,
                     'scope': '全市城镇常住居民', 'sourceId': source['id'], 'sourceUrl': source['url'],
                     'incomeDefinition': '城镇常住居民人均可支配收入，不是就业人员工资'}]
    raise ValueError('未登记的解析器')


def collect(config, offline=False, refresh=False, interval=1.0):
    cache = ROOT / 'backend/data/city-sources'
    raw = cache / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    output = ROOT / 'docs/data/cities/china-city-data.json'
    old = json.loads(output.read_text()) if output.exists() else {'records': [], 'incomes': [], 'sources': []}
    old_sources = {s['id']: s for s in old['sources']}
    all_records, incomes, sources = [], [], []
    session = requests.Session()
    session.headers['User-Agent'] = 'HousingResearch/2.1 (public aggregate statistics)'
    for spec in config['sources']:
        source = {k: v for k, v in spec.items() if k not in ['reviewedRecords', 'reviewedIncomes', 'reviewedSha256']}
        try:
            parsed = urlparse(spec['url'])
            if parsed.scheme != 'https' or parsed.hostname not in config['allowedHosts'] or parsed.username or parsed.port:
                raise ValueError('来源不是已登记的官方HTTPS网址')
            key = hashlib.sha256(spec['url'].encode()).hexdigest()
            metadata = cache / (key + '.json')
            meta = json.loads(metadata.read_text()) if metadata.exists() else None
            recent = meta and (datetime.now(timezone.utc).timestamp() - meta['timestamp']) < 86400
            if spec['parser'] == 'reviewed-evidence':
                body = (ROOT / spec['evidenceFile']).read_bytes()
                meta = {'file': spec['evidenceFile']}
                fetched_at = spec['reviewedAt']
            elif meta and (offline or (recent and not refresh)):
                body = (raw / meta['file']).read_bytes()
                if hashlib.sha256(body).hexdigest() != meta['sha256']:
                    raise ValueError('缓存原文哈希不一致')
                fetched_at = meta['fetchedAt']
            elif offline:
                raise ValueError('没有该来源的离线原文')
            else:
                time.sleep(interval)
                with session.get(spec['url'], timeout=(10, 25), stream=True, allow_redirects=False) as response:
                    response.raise_for_status()
                    if response.status_code != 200:
                        raise ValueError('官方入口发生重定向，需人工确认新地址')
                    content = bytearray()
                    for chunk in response.iter_content(65536):
                        content.extend(chunk)
                        if len(content) > 10000000:
                            raise ValueError('原文超过10MB读取上限')
                    body = bytes(content)
                fetched_at = datetime.now(timezone.utc).isoformat()
                digest = hashlib.sha256(body).hexdigest()
                file = digest + ('.pdf' if spec['url'].endswith('.pdf') else '.html')
                (raw / file).write_bytes(body)
                meta = {'file': file, 'sha256': digest, 'fetchedAt': fetched_at,
                        'timestamp': datetime.now(timezone.utc).timestamp(), 'url': spec['url']}
                metadata.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
            records, income = parse_source(spec, body)
            all_records.extend(normalized_record(r, spec) for r in records)
            incomes.extend(income)
            if spec['parser'] == 'reviewed-evidence':
                source.update({'status': 'reviewed-evidence', 'rawSha256': None,
                               'evidenceSha256': hashlib.sha256(body).hexdigest(), 'fetchedAt': fetched_at,
                               'evidenceNote': ('统计公报转载网页核读摘录；媒体及原发布者见来源署名，摘录哈希不是原文HTML哈希。'
                                                if spec.get('sourceType') == 'official-bulletin-republication' else
                                                '官方公开网页核读摘录；摘录哈希不是原文HTML哈希。')})
            else:
                source.update({'status': 'collected', 'rawSha256': hashlib.sha256(body).hexdigest(),
                               'fetchedAt': fetched_at, 'rawSnapshot': meta['file']})
            print(f"{spec['id']}: {len(records)} records, {len(income)} income values", flush=True)
        except Exception as error:
            previous = old_sources.get(spec['id'], {})
            source = {**previous, **source, 'status': 'needs_review' if previous else 'unavailable',
                      'lastAttemptAt': datetime.now(timezone.utc).isoformat(), 'error': str(error)[:350]}
            all_records.extend(r for r in old['records'] if r['sourceId'] == spec['id'])
            incomes.extend(r for r in old.get('incomes', []) if r['sourceId'] == spec['id'])
            print(f"{spec['id']}: {source['status']} - {source['error']}", flush=True)
        sources.append(source)
    session.close()
    baselines = []
    for r in all_records:
        if r.get('excludeFromAnnualAffordability') or r['district'] or r['frequency'] != 'annual' or r['houseType'] != 'new-residential' or not r['priceCnyPerSqm']:
            continue
        matched = next((inc for inc in incomes if inc['city'] == r['city'] and str(inc['year']) == r['period']), None)
        if matched:
            baselines.append({'id': r['id'], 'city': r['city'], 'year': matched['year'],
                              'priceCnyPerSqm': r['priceCnyPerSqm'],
                              'urbanDisposableIncomeCnyPerYear': matched['urbanDisposableIncomeCnyPerYear'],
                              'salesAreaSqm': r['areaSqm'], 'salesAmountCny': r['amountCny'],
                              'salesSourceId': r['sourceId'], 'incomeSourceId': matched['sourceId'], 'scope': r['scope']})
    data = {'schemaVersion': 1, 'title': '中国城市官方住宅交易与同年收入观察',
            'retrievedAt': config['asOf'], 'scope': '首批城市和公开分区，不代表全国所有城市已接入',
            'cities': config['cities'], 'sources': sources, 'records': all_records, 'incomes': incomes,
            'annualAffordability': baselines, 'unavailableSources': config.get('unavailableSources', []),
            'methodology': config['methodology'], 'recentCoverage': config.get('recentCoverage', {})}
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temp.replace(output)
    (output.parent / 'china-city-data.js').write_text('window.CHINA_CITY_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'Published {len(all_records)} source observations, {len(baselines)} same-year affordability baselines.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/city-sources.json')
    parser.add_argument('--offline', action='store_true', help='Rebuild from retained source snapshots only')
    parser.add_argument('--refresh', action='store_true', help='Read original sources again; changed reviewed sources require review')
    args = parser.parse_args()
    collect(json.loads(args.config.read_text()), args.offline, args.refresh)
