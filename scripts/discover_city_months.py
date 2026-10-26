"""Discover and collect closed-month Wuhan/Shijiazhuang public residential tables.

Updates registered sources only after the returned period, residential columns and
district totals have been read successfully. Missing months are reported, not filled.
"""
import argparse
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from collect_city_data import ROOT, compact, parse_source


def months(start, end):
    y, m = map(int, start.split('-'))
    result = []
    while f'{y:04d}-{m:02d}' <= end:
        result.append(f'{y:04d}-{m:02d}')
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return result


def main(start, end):
    import re
    requested = months(start, end)
    if not requested or len(requested) > 36:
        raise ValueError('每次需要1至36个完整月份')
    config_path = ROOT / 'configs/city-sources.json'
    config = json.loads(config_path.read_text())
    cache = ROOT / 'backend/data/city-sources'
    (cache / 'raw').mkdir(parents=True, exist_ok=True)
    host_locks = {host: threading.Lock() for host in ['zgj.wuhan.gov.cn', 'zjj.sjz.gov.cn']}
    last_request = {host: 0.0 for host in host_locks}

    def fetch(url):
        host = urlparse(url).hostname
        if host not in host_locks or not url.startswith('https://'):
            raise ValueError('未登记的公开来源')
        key = hashlib.sha256(url.encode()).hexdigest()
        meta_file = cache / (key + '.json')
        if meta_file.exists():
            meta = json.loads(meta_file.read_text())
            if datetime.now(timezone.utc).timestamp() - meta['timestamp'] < 86400:
                body = (cache / 'raw' / meta['file']).read_bytes()
                if hashlib.sha256(body).hexdigest() == meta['sha256']:
                    return body, meta
        with host_locks[host]:
            time.sleep(max(0, 1.0 - (time.monotonic() - last_request[host])))
            last_request[host] = time.monotonic()
        r = requests.get(url, timeout=(8, 22), headers={'User-Agent': 'HousingResearch/2.2 (public aggregate statistics)'}, allow_redirects=False)
        if r.status_code != 200 or len(r.content) > 5000000:
            raise ValueError(f'来源返回HTTP {r.status_code}或超过5MB')
        body = r.content
        digest = hashlib.sha256(body).hexdigest()
        meta = {'url': url, 'file': digest + '.html', 'sha256': digest,
                'fetchedAt': datetime.now(timezone.utc).isoformat(), 'timestamp': datetime.now(timezone.utc).timestamp()}
        (cache / 'raw' / meta['file']).write_bytes(body)
        meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
        return body, meta

    index_root = 'https://zgj.wuhan.gov.cn/xxgk/xxgkml/sjfb/spzfxysydjcjb/'
    jobs = {}
    for index_url in [index_root, index_root + 'index_1.shtml']:
        body, _ = fetch(index_url)
        for a in BeautifulSoup(body, 'lxml').select('a[href]'):
            match = re.fullmatch(r'(\d{4})年(\d{1,2})月新建商品房成交统计情况', compact(a.get_text()))
            if not match:
                continue
            period = f'{match[1]}-{int(match[2]):02d}'
            url = urljoin(index_url, a['href'])
            if period in requested and urlparse(url).hostname == 'zgj.wuhan.gov.cn':
                key = 'wuhan-housing-' + period.replace('-', '')
                jobs[key] = {'id': key, 'url': url, 'title': f'武汉{period}新建商品房成交统计情况',
                             'provider': '武汉市住房和城市更新局', 'kind': 'housing-department',
                             'cityCode': '420100', 'period': period, 'parser': 'wuhan-monthly', 'indexUrl': index_url}
    for period in requested:
        key = 'sjz-' + period
        jobs[key] = {'id': key, 'url': 'https://zjj.sjz.gov.cn/plus/list.php?tid=192&y=' + period,
                     'title': f'石家庄{period}房屋网签成交数量', 'provider': '石家庄市住房和城乡建设局',
                     'kind': 'housing-department', 'cityCode': '130100', 'period': period, 'parser': 'shijiazhuang'}
    successful, failed = [], []
    for period in requested:
        if 'wuhan-housing-' + period.replace('-', '') not in jobs:
            failed.append({'period': period, 'cityCode': '420100', 'url': index_root,
                           'reason': '已读取的官方索引未发现该月文章，未补造记录。'})

    def collect(spec):
        try:
            body, meta = fetch(spec['url'])
            records, _ = parse_source(spec, body)
            if not records:
                raise ValueError('未获得可核验的住宅行')
            soup = BeautifulSoup(body, 'lxml')
            date_tag = soup.find('meta', attrs={'name': re.compile('pubdate', re.I)})
            spec['publishedAt'] = date_tag.get('content') if date_tag else None
            spec['verifiedAt'] = config['asOf']
            print(f"{spec['id']}: {len(records)} observations", flush=True)
            return spec, None
        except Exception as error:
            failure = {'id': spec['id'], 'period': spec['period'], 'cityCode': spec['cityCode'], 'url': spec['url'], 'reason': str(error)[:250]}
            print(f"{spec['id']}: unavailable - {failure['reason']}", flush=True)
            return None, failure

    with ThreadPoolExecutor(max_workers=3) as pool:
        for spec, error in pool.map(collect, jobs.values()):
            if spec:
                successful.append(spec)
            else:
                failed.append(error)
    registered = {s['id']: s for s in config['sources']}
    for spec in successful:
        registered[spec['id']] = spec
    config['sources'] = list(registered.values())
    config['allowedHosts'] = sorted(set(config['allowedHosts']) | set(host_locks))
    config['recentCoverage'] = {'start': start, 'end': end, 'verifiedAt': config['asOf'],
                                'periods': {}, 'failed': failed, 'note': '只计核对成功的公开月份，不将缺失月份补零。'}
    for name, code in [('武汉', '420100'), ('石家庄', '130100')]:
        periods = sorted(s['period'] for s in successful if s['cityCode'] == code)
        config['recentCoverage']['periods'][name] = periods
        city = next(c for c in config['cities'] if c['id'] == code)
        city['coverageNote'] = f'已核对{start}至{end}期间{len(periods)}个月住宅表，含原表分区；未公开金额，不计算均价。统计范围见记录。'
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    print(f'Registered {len(successful)} verified monthly tables; {len(failed)} failed requests.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    args = parser.parse_args()
    import re
    if not all(re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', p) for p in [args.start, args.end]):
        raise SystemExit('Use YYYY-MM for start and end.')
    current_month = datetime.now(timezone.utc).strftime('%Y-%m')
    if args.end >= current_month:
        raise SystemExit('Only completed months may be collected.')
    main(args.start, args.end)
