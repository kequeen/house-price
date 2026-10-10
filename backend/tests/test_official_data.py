import asyncio
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.catalog import CITY_CATALOG
from app.collectors.http import FetchedPage
from app.collectors.nbs import parse_nbs, validate_period
from app.collectors.housing import parse_beijing, parse_shijiazhuang
from app.database import Base, get_db
from app.main import app
from app.models.official import City, HousingObservation, PriceObservation, SourceDocument, SyncRun
from app.services.ingest import ingest_prices, ingest_housing
from app.services.series import build_series
from app.services.sync import create_run, SyncAlreadyRunning

FIXTURES = Path(__file__).parent / 'fixtures'


def fixture(name):
    return (FIXTURES / f'{name}.html').read_text()


def page(name, digest='a' * 64):
    return FetchedPage(f'https://www.stats.gov.cn/{name}', fixture(name).encode(), digest, 'raw/test.html', datetime(2026, 10, 3))


class ParserTests(unittest.TestCase):
    def test_all_cities_and_both_house_types(self):
        result = parse_nbs(fixture('nbs'), '2026-01')
        self.assertEqual(len(result['records']), 140)
        self.assertEqual(len({r['city'] for r in result['records']}), 70)
        self.assertTrue(set(CITY_CATALOG).issubset({r['city'] for r in result['records']}))
        beijing = {r['house_type']: r for r in result['records'] if r['city'] == '北京'}
        self.assertEqual(beijing['new']['mom_index'], 99.7)
        self.assertEqual(beijing['new']['yoy_index'], 97.6)
        self.assertEqual(beijing['second_hand']['mom_index'], 99.8)
        self.assertEqual(beijing['second_hand']['yoy_index'], 91.3)

    def test_desktop_mobile_conflict_is_rejected(self):
        soup = BeautifulSoup(fixture('nbs'), 'lxml')
        table = soup.find_all('table')[6]
        for td in table.find_all('td'):
            if td.get_text(strip=True) == '99.7':
                td.clear(); td.append('99.6'); break
        with self.assertRaisesRegex(ValueError, '不一致'):
            parse_nbs(str(soup))

    def test_wrong_month_rejected(self):
        with self.assertRaisesRegex(ValueError, '不匹配'):
            parse_nbs(fixture('nbs'), '2026-02')

    def test_challenge_page_rejected(self):
        with self.assertRaises(ValueError):
            parse_nbs('<html><title>安全验证</title></html>')

    def test_invalid_index_rejected(self):
        with self.assertRaises(ValueError):
            parse_nbs(fixture('nbs').replace('99.7', '999.7'))

    def test_incomplete_release_rejected(self):
        soup = BeautifulSoup(fixture('nbs'), 'lxml')
        for table in soup.find_all('table')[1:]:
            table.decompose()
        with self.assertRaisesRegex(ValueError, '不完整'):
            parse_nbs(str(soup))

    def test_period_guard_rejects_future_and_bad_month(self):
        for period in ['2026-10', '2026-12', '2026-13', '2026-00', '2010-12']:
            with self.subTest(period=period), self.assertRaises(ValueError):
                validate_period(period, date(2026, 10, 3))
        self.assertEqual(validate_period('2026-09', date(2026, 10, 3)), '2026-09')

    def test_shijiazhuang_residential_columns(self):
        records = parse_shijiazhuang(fixture('sjz'), '2026-06')['records']
        self.assertEqual(records[0]['transaction_count'], 3235)
        self.assertEqual(records[0]['area_sqm'], 408397.73)
        self.assertEqual(records[1]['transaction_count'], 4880)
        self.assertIn('藁城区', records[0]['scope'])
        self.assertNotEqual(records[0]['transaction_count'], 4709)  # 不把全部商品房当成住宅。

    def test_shijiazhuang_sum_mismatch(self):
        changed = fixture('sjz').replace('408397.73', '408398.73')
        with self.assertRaisesRegex(ValueError, '不一致'):
            parse_shijiazhuang(changed, '2026-06')

    def test_shijiazhuang_unpublished_is_not_zero(self):
        with self.assertRaises(ValueError):
            parse_shijiazhuang('<h1>2026年06月房屋网签成交数量</h1><table>商品房其中住宅存量住房</table>', '2026-06')

    def test_beijing_month_and_annual_units(self):
        records = parse_beijing(fixture('bj'))['records']
        monthly = next(r for r in records if r['frequency'] == 'month')
        self.assertEqual(monthly['period'], '2025-10')
        self.assertEqual(monthly['transaction_count'], 12087)
        self.assertEqual(monthly['area_sqm'], 1083486.46)
        annual = next(r for r in records if r['period'] == '2024' and r['house_type'] == 'new')
        self.assertEqual(annual['transaction_count'], 51100)
        self.assertAlmostEqual(annual['area_sqm'], 6009000)

    def test_beijing_annual_house_type_labels_required(self):
        html = fixture('bj').replace('我市新建商品房网签情况', '未识别标签')
        with self.assertRaisesRegex(ValueError, '标签'):
            parse_beijing(html)


class SeriesTests(unittest.TestCase):
    def rows(self):
        return [SimpleNamespace(period=p, mom_index=m, yoy_index=y, source_id=1)
                for p, m, y in [('2024-01', 99.0, 100.0), ('2024-02', 100.5, 98.0), ('2024-03', 99.0, 97.0)]]

    def test_relative_index_compounds_after_baseline(self):
        points = build_series(self.rows(), '2024-01', '2024-03', 'relative_index')
        self.assertEqual([p['value'] for p in points], [100.0, 100.5, 99.495])

    def test_missing_month_breaks_relative_chain(self):
        rows = self.rows()[::2]
        points = build_series(rows, '2024-01', '2024-03', 'relative_index')
        self.assertEqual([p['value'] for p in points], [100.0, None, None])

    def test_missing_baseline_does_not_rebase_other_city(self):
        points = build_series(self.rows()[1:], '2024-01', '2024-03', 'relative_index')
        self.assertEqual([p['value'] for p in points], [None, None, None])

    def test_zero_change_and_missing_are_distinct(self):
        points = build_series(self.rows()[::2], '2024-01', '2024-03', 'yoy_change')
        self.assertEqual([p['value'] for p in points], [0.0, None, -3.0])


class StorageAndApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.sessions() as db:
            db.add_all([City(name=city, **meta) for city, meta in CITY_CATALOG.items()]); db.commit()
        def override():
            with self.sessions() as db:
                yield db
        app.dependency_overrides[get_db] = override

    def tearDown(self):
        app.dependency_overrides.clear()
        self.engine.dispose()

    def load_prices(self):
        with self.sessions() as db:
            return ingest_prices(db, page('nbs'), parse_nbs(fixture('nbs')), 'test-v1')

    def request(self, path, query=''):
        async def run():
            messages = []
            async def receive():
                return {'type': 'http.request', 'body': b'', 'more_body': False}
            async def send(message):
                messages.append(message)
            scope = {'type':'http','asgi':{'version':'3.0'},'http_version':'1.1','method':'GET',
                     'scheme':'http','path':path,'raw_path':path.encode(),'query_string':query.encode(),
                     'root_path':'','headers':[],'server':('test',80),'client':('test',1)}
            await app(scope, receive, send)
            status = next(m['status'] for m in messages if m['type'] == 'http.response.start')
            body = b''.join(m.get('body', b'') for m in messages if m['type'] == 'http.response.body')
            return status, body
        return asyncio.run(run())

    def test_repeat_ingest_is_idempotent(self):
        self.assertEqual(self.load_prices(), 140)
        self.assertEqual(self.load_prices(), 0)
        with self.sessions() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(PriceObservation)), 140)
            self.assertEqual(db.scalar(select(func.count()).select_from(SourceDocument)), 1)

    def test_official_revision_updates_observation_keeps_both_sources(self):
        self.load_prices()
        parsed = parse_nbs(fixture('nbs')); parsed['records'][0]['mom_index'] = 99.6
        with self.sessions() as db:
            ingest_prices(db, page('nbs', 'b'*64), parsed, 'test-v2')
            self.assertEqual(db.scalar(select(func.count()).select_from(PriceObservation)), 140)
            self.assertEqual(db.scalar(select(func.count()).select_from(SourceDocument)), 2)
            self.assertEqual(db.scalar(select(PriceObservation.mom_index).where(PriceObservation.city == '北京', PriceObservation.house_type == 'new')), 99.6)

    def test_housing_repeat_ingest_and_frequency(self):
        parsed = parse_beijing(fixture('bj'))
        with self.sessions() as db:
            self.assertEqual(ingest_housing(db, page('bj'), parsed, 'beijing', 'test'), 11)
            self.assertEqual(ingest_housing(db, page('bj'), parsed, 'beijing', 'test'), 0)
        status, body = self.request('/api/housing', 'city=%E5%8C%97%E4%BA%AC&frequency=month')
        self.assertEqual(status, 200)
        import json
        self.assertEqual(json.loads(body)['total'], 1)

    def test_overview_and_all_35_cities_without_truncation(self):
        import json
        self.load_prices()
        status, body = self.request('/api/overview')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['covered_city_count'], 35)
        self.assertEqual(json.loads(body)['price_record_count'], 70)
        _, body = self.request('/api/observations')
        self.assertEqual(json.loads(body)['total'], 35)
        self.assertTrue(all(item['source']['url'] for item in json.loads(body)['items']))

    def test_invalid_house_type_and_city_rejected(self):
        self.load_prices()
        for path, query in [('/api/series', 'house_type=unknown'), ('/api/series', 'cities=unknown'), ('/api/series', 'start=2026-13'), ('/api/housing', 'frequency=day')]:
            with self.subTest(query=query):
                self.assertEqual(self.request(path, query)[0], 422)

    def test_empty_database_endpoints_are_safe(self):
        for endpoint in ['/api/overview', '/api/cities', '/api/series', '/api/observations', '/api/housing', '/api/sources', '/api/documents', '/api/export/prices']:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.request(endpoint)[0], 200)

    def test_invalid_period_is_rejected_even_when_database_empty(self):
        self.assertEqual(self.request('/api/series', 'start=2026-13')[0], 422)

    def test_document_pagination_reports_actual_total(self):
        import json
        self.load_prices()
        status, body = self.request('/api/documents', 'page=2&page_size=1')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['total'], 1)
        self.assertEqual(json.loads(body)['items'], [])

    def test_csv_contains_provenance_and_all_selected_rows(self):
        self.load_prices()
        status, body = self.request('/api/export/prices')
        self.assertEqual(status, 200)
        self.assertIn('来源链接'.encode(), body)
        self.assertEqual(len(body.decode('utf-8-sig').splitlines()), 36)

    def test_sync_lock_is_shared_by_api_and_cli(self):
        with patch('app.services.sync.SessionLocal', self.sessions):
            first = create_run('2024-01', '2024-12')
            with self.assertRaises(SyncAlreadyRunning):
                create_run('2024-01', '2024-12')
            with self.sessions() as db:
                run = db.get(SyncRun, first); run.status = 'succeeded'; db.commit()
            self.assertNotEqual(create_run('2024-01', '2024-12'), first)


if __name__ == '__main__':
    unittest.main()
