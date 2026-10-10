"""限速、TLS校验、官方域名白名单及可审计原始快照。"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import json
import time
import requests
from app.config import settings

ALLOWED_HOSTS = {'www.stats.gov.cn', 'zjw.beijing.gov.cn', 'zjj.sjz.gov.cn'}


@dataclass(frozen=True)
class FetchedPage:
    url: str
    body: bytes
    sha256: str
    snapshot_path: str
    fetched_at: datetime

    @property
    def html(self):
        return self.body.decode('utf-8-sig')


class OfficialClient:
    def __init__(self, data_dir=None, interval=None):
        self.data_dir = Path(data_dir or settings.DATA_DIR)
        self.interval = settings.REQUEST_INTERVAL if interval is None else interval
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'HousingResearch/2.0 (public statistical data)', 'Accept': 'text/html'})
        self.last_request = 0.0
        for folder in ['raw', 'cache']:
            (self.data_dir / folder).mkdir(parents=True, exist_ok=True)

    def close(self):
        self.session.close()

    def fetch(self, url, refresh=False, max_age=None):
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.port:
            raise ValueError('只允许已登记的官方HTTPS数据源')
        key = hashlib.sha256(url.encode()).hexdigest()
        metadata_file = self.data_dir / 'cache' / f'{key}.json'
        if metadata_file.exists() and not refresh:
            meta = json.loads(metadata_file.read_text())
            age = time.time() - meta['timestamp']
            snapshot = self.data_dir / meta['snapshot_path']
            if snapshot.exists() and (max_age is None or age < max_age):
                body = snapshot.read_bytes()
                if hashlib.sha256(body).hexdigest() == meta['sha256']:
                    return FetchedPage(url, body, meta['sha256'], meta['snapshot_path'], datetime.fromisoformat(meta['fetched_at']))
        for attempt in range(3):
            time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
            try:
                self.last_request = time.monotonic()
                with self.session.get(url, timeout=(10, 25), stream=True, allow_redirects=False) as response:
                    response.raise_for_status()
                    if response.status_code != 200:
                        raise ValueError(f'官方页面发生重定向或返回异常状态：{response.status_code}')
                    body = bytearray()
                    for chunk in response.iter_content(65536):
                        body.extend(chunk)
                        if len(body) > 5_000_000:
                            raise ValueError('官方页面超过5MB读取限制')
                body = bytes(body)
                digest = hashlib.sha256(body).hexdigest()
                path = f'raw/{digest}.html'
                (self.data_dir / path).write_bytes(body)
                fetched = datetime.now(timezone.utc).replace(tzinfo=None)
                metadata_file.write_text(json.dumps({'url': url, 'sha256': digest, 'snapshot_path': path,
                    'fetched_at': fetched.isoformat(), 'timestamp': time.time()}, ensure_ascii=False))
                return FetchedPage(url, body, digest, path, fetched)
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(0.5 * (attempt + 1))
