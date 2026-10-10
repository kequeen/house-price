import math
import re
from bs4 import BeautifulSoup
from app.collectors.nbs import normalize, validate_period

PARSER_VERSION = 'housing-html-v1'
BEIJING_URL = 'https://zjw.beijing.gov.cn/bjjs/fdcjy/wqht/fcsjtj/index.shtml'
SJZ_URL = 'https://zjj.sjz.gov.cn/plus/list.php?tid=192&y={period}'


def nonnegative(value):
    number = float(normalize(value).replace(',', ''))
    if not math.isfinite(number) or number < 0:
        raise ValueError('网签数据必须为有限非负数')
    return number


def parse_shijiazhuang(html, expected_period):
    soup = BeautifulSoup(html, 'lxml')
    text = normalize(soup.get_text())
    match = re.search(r'(\d{4})年(\d{2})月房屋网签成交数量', text)
    if not match or f'{match[1]}-{match[2]}' != expected_period:
        raise ValueError('住建局未公布该月表格，或返回了其他月份的数据')
    validate_period(expected_period)
    table = soup.find('table')
    if not table or not all(x in normalize(table.get_text()) for x in ['商品房', '其中住宅', '存量住房']):
        raise ValueError('网签表头与已验证的统计口径不一致')
    districts, total = [], None
    for row in table.find_all('tr'):
        cells = [normalize(td.get_text()) for td in row.find_all('td', recursive=False)]
        if len(cells) == 7:
            values = [nonnegative(value) for value in cells[1:]]
            if cells[0] == '合计':
                total = values
            else:
                districts.append((cells[0], values))
    if not total or not districts:
        raise ValueError('网签表缺少合计或分区行')
    for i, official_total in enumerate(total):
        if abs(sum(values[i] for _, values in districts) - official_total) > 0.1:
            raise ValueError('网签合计与分区数据不一致')
    scope = '、'.join(name for name, _ in districts)
    return {'title': f'石家庄{expected_period}房屋网签成交统计', 'published_at': None,
            'records': [{'city': '石家庄', 'period': expected_period, 'frequency': 'month',
                         'house_type': kind, 'scope': scope, 'provider': 'shijiazhuang',
                         'transaction_count': total[column], 'area_sqm': total[column + 1],
                         'note': '新房取商品房中的住宅列；二手房取存量住房列。范围为原表列出的区。'}
                        for kind, column in [('new', 2), ('second_hand', 4)]]}


def parse_beijing(html):
    soup = BeautifulSoup(html, 'lxml')
    text = normalize(soup.get_text())
    records = []
    raw_text = soup.get_text(' ', strip=True)
    monthly = re.search(r'(\d{4})年(\d{1,2})月存量房网上签约\s*网上签约套数：\s*[\d.]+\s*网上签约面积\(m2\)：\s*[\d.]+\s*住宅签约套数：\s*([\d.]+)\s*住宅签约面积\(m2\)：\s*([\d.]+)(?=\s|$)', raw_text)
    if monthly:
        period = f'{int(monthly[1]):04d}-{int(monthly[2]):02d}'
        validate_period(period)
        records.append({'city': '北京', 'period': period, 'frequency': 'month',
                        'house_type': 'second_hand', 'scope': '全市住宅', 'provider': 'beijing',
                        'transaction_count': nonnegative(monthly[3]), 'area_sqm': nonnegative(monthly[4]),
                        'note': '采用明确标注月份的住宅签约列，不采用当日或全部物业数据。'})
    annual = [table for table in soup.find_all('table') if '住宅套数' in normalize(table.get_text()) and '非住宅面积' in normalize(table.get_text())]
    if len(annual) == 2 and '近五年房屋网上签约统计' in text and '单位:万套、万平方米' in text:
        for table in annual:
            box = table.parent.parent
            labels = [normalize(a.get_text()) for a in box.find_all('a')
                      if re.search(r'我市(新建商品房网签情况|存量房交易情况)', normalize(a.get_text()))]
            panels = [t for t in box.find_all('table') if t in annual]
            if len(labels) != 2 or len(panels) != 2:
                raise ValueError('北京年度表的住宅类型标签无法对应，拒绝推测口径')
            label = labels[panels.index(table)]
            kind = 'new' if '新建商品房网签情况' in label else 'second_hand'
            for row in table.find_all('tr'):
                cells = [normalize(td.get_text()) for td in row.find_all('td', recursive=False)]
                if len(cells) == 4 and re.fullmatch(r'20\d{2}年', cells[0]):
                    period = cells[0][:4]
                    validate_period(period + '-12')
                    records.append({'city': '北京', 'period': period, 'frequency': 'year',
                                    'house_type': kind, 'scope': '全市住宅', 'provider': 'beijing',
                                    'transaction_count': round(nonnegative(cells[1]) * 10000, 2),
                                    'area_sqm': round(nonnegative(cells[2]) * 10000, 2),
                                    'note': '原表单位为万套、万平方米，已换算；原始年度数据存在取整。'})
    if not records:
        raise ValueError('北京官方网页未包含可核验期间和口径的成交表')
    return {'title': '北京市住建委房产数据统计', 'published_at': None, 'records': records}
