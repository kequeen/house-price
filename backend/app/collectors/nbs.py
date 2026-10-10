from datetime import date
from urllib.parse import urljoin
import math
import re
from bs4 import BeautifulSoup
from app.catalog import CITY_CATALOG

PARSER_VERSION = 'nbs-html-v1'
LIST_URL = 'https://www.stats.gov.cn/sj/zxfb/'


def normalize(text):
    return re.sub(r'\s+', '', text)


def previous_month(today=None):
    today = today or date.today()
    return f'{today.year - (today.month == 1):04d}-{12 if today.month == 1 else today.month - 1:02d}'


def validate_period(period, today=None):
    if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', period):
        raise ValueError('月份必须是YYYY-MM')
    if period < '2011-01' or period > previous_month(today):
        raise ValueError('月份必须在2011-01与最近已结束月份之间')
    return period


def month_range(start, end):
    year, month = map(int, start.split('-'))
    while (period := f'{year:04d}-{month:02d}') <= end:
        yield period
        month += 1
        if month == 13:
            year, month = year + 1, 1


def period_from_title(title):
    match = re.search(r'(\d{4})年(\d{1,2})月份?70个大中城市.*销售价格变动情况', normalize(title))
    return f'{int(match[1]):04d}-{int(match[2]):02d}' if match else None


def discover_releases(client, start, end, progress=lambda _: None, max_pages=160, refresh=False):
    releases = {}
    for page_no in range(max_pages):
        url = LIST_URL if page_no == 0 else urljoin(LIST_URL, f'index_{page_no}.html')
        progress(f'查找国家统计局历史公告 · 第 {page_no + 1} 页')
        page = client.fetch(url, refresh=refresh, max_age=86400)
        soup = BeautifulSoup(page.html, 'lxml')
        found = []
        for link in soup.select('a[href]'):
            title = link.get('title') or link.get_text(' ', strip=True)
            period = period_from_title(title)
            if period:
                found.append(period)
                if start <= period <= end:
                    releases.setdefault(period, urljoin(url, link['href']))
        if found and min(found) < start:
            return releases
        if not soup.title or '国家统计局' not in soup.title.get_text():
            raise ValueError(f'历史公告目录无法解析：{url}')
    raise ValueError(f'已扫描{max_pages}页，尚未到达起始月份；请缩小范围后分批同步')


def index_number(text):
    value = normalize(text)
    if value in {'', '-', '--', '—', '…'}:
        return None
    if not re.fullmatch(r'\d+(\.\d+)?', value):
        raise ValueError(f'无法识别价格指数：{text}')
    number = float(value)
    if not math.isfinite(number) or not 0 < number < 300:
        raise ValueError(f'价格指数超出校验范围：{number}')
    return number


def parse_nbs(html, expected_period=None):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    period = period_from_title(title)
    if not period:
        raise ValueError('页面不是国家统计局70城住宅价格公告')
    validate_period(period)
    if expected_period and period != expected_period:
        raise ValueError(f'公告月份不匹配：要求{expected_period}，实际{period}')
    aggregates = {}
    for table in soup.find_all('table'):
        heading = next((normalize(p.get_text()) for p in table.find_all_previous('p')
                        if re.match(r'表[1-4][：:]', normalize(p.get_text()))), '')
        if not re.match(r'表[12][：:]', heading) or '分类' in heading:
            continue
        house_type = 'new' if heading.startswith(('表1：', '表1:')) else 'second_hand'
        header = normalize(table.get_text(' ', strip=True))
        if '环比' not in header or '同比' not in header or '90m' in header or '90㎡' in header:
            continue
        rows = {}
        for tr in table.find_all('tr'):
            cells = [normalize(td.get_text(' ', strip=True)) for td in tr.find_all(['td', 'th'], recursive=False)]
            for position, cell in enumerate(cells):
                if re.fullmatch(r'[\u4e00-\u9fff]{2,5}', cell) and cell not in {'城市', '环比', '同比', '定基'} and position + 2 < len(cells):
                    if re.fullmatch(r'\d+(\.\d+)?|--?|—|…', cells[position + 1]):
                        if cell in rows:
                            raise ValueError(f'同一表格存在重复城市：{cell}')
                        rows[cell] = (index_number(cells[position + 1]), index_number(cells[position + 2]))
        if len(rows) == 70 and set(CITY_CATALOG).issubset(rows):
            # 面积分档表也有70城，明确只接受每城2或3列指标的总指数表。
            data_rows = [tr for tr in table.find_all('tr') if any(normalize(td.get_text()) in CITY_CATALOG for td in tr.find_all('td', recursive=False))]
            if data_rows and max(len(tr.find_all(['td', 'th'], recursive=False)) for tr in data_rows) <= 8:
                if house_type in aggregates and aggregates[house_type] != rows:
                    raise ValueError('桌面与移动版价格表数据不一致，拒绝入库')
                aggregates[house_type] = rows
    if len(aggregates) != 2 or set(aggregates['new']) != set(aggregates['second_hand']):
        raise ValueError(f'新房/二手房总指数表不完整：识别到{len(aggregates)}张70城表')
    body = soup.get_text(' ', strip=True)
    published = re.search(r'(20\d{2})[/-](\d{2})[/-](\d{2})\s+\d{2}:\d{2}', body)
    records = [{'city': city, 'period': period, 'house_type': house_type,
                'mom_index': values[0], 'yoy_index': values[1], 'provider': 'nbs'}
               for house_type, rows in aggregates.items()
               for city, values in rows.items()]
    return {'title': title, 'period': period, 'published_at': '-'.join(published.groups()) if published else None, 'records': records}
