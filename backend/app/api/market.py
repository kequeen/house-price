import csv
import io
import json
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.catalog import CITY_CATALOG, LOCAL_SOURCES, TIER_SOURCE_URL
from app.collectors.nbs import previous_month, validate_period
from app.config import settings
from app.database import get_db
from app.models.official import City, HousingObservation, PriceObservation, SourceDocument, SyncRun
from app.services.series import build_series
from app.services.sync import create_run, run_sync, SyncAlreadyRunning

router = APIRouter(prefix='/api', tags=['official-market'])
HouseType = Literal['new', 'second_hand']
Metric = Literal['yoy_change', 'mom_change', 'relative_index']


def document_json(row):
    return {'id': row.id, 'provider': row.provider, 'title': row.title, 'url': row.url,
            'published_at': row.published_at, 'fetched_at': row.fetched_at.isoformat() + 'Z',
            'sha256': row.sha256, 'parser_version': row.parser_version,
            'snapshot_url': f'/api/documents/{row.id}/snapshot'}


def run_json(run):
    return {'id': run.id, 'status': run.status, 'start_period': run.start_period,
            'end_period': run.end_period, 'started_at': run.started_at.isoformat() + 'Z',
            'finished_at': run.finished_at.isoformat() + 'Z' if run.finished_at else None,
            'progress': run.progress, 'price_records': run.price_records,
            'housing_records': run.housing_records, 'errors': json.loads(run.errors_json)}


def selected_cities(value, max_cities=35):
    cities = list(dict.fromkeys(x.strip() for x in value.split(',') if x.strip())) if value else list(CITY_CATALOG)
    if not cities or len(cities) > max_cities or not set(cities).issubset(CITY_CATALOG):
        raise HTTPException(422, f'请选择1至{max_cities}个已登记的一、二线城市')
    return cities


def price_bounds(db, start, end):
    try:
        for period in [start, end]:
            if period is not None:
                validate_period(period)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    earliest, latest = db.execute(select(func.min(PriceObservation.period), func.max(PriceObservation.period))).one()
    if not latest:
        return None, None
    start, end = start or earliest, end or latest
    try:
        validate_period(start)
        validate_period(end)
        if start > end:
            raise ValueError('起始月份不能晚于结束月份')
        if int(end[:4]) * 12 + int(end[5:]) - int(start[:4]) * 12 - int(start[5:]) > 240:
            raise ValueError('一次查询最多241个月')
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return start, end


@router.get('/overview')
def overview(db: Session = Depends(get_db)):
    target = list(CITY_CATALOG)
    periods = list(db.scalars(select(PriceObservation.period).distinct().order_by(PriceObservation.period)))
    latest = periods[-1] if periods else None
    rows = db.scalars(select(PriceObservation).where(PriceObservation.city.in_(target), PriceObservation.period == latest)).all() if latest else []
    complete = {city for city in target if {r.house_type for r in rows if r.city == city} == {'new', 'second_hand'}}
    housing_cities = list(db.scalars(select(HousingObservation.city).distinct()))
    latest_run = db.scalar(select(SyncRun).order_by(SyncRun.id.desc()).limit(1))
    return {'target_city_count': 35, 'covered_city_count': len(complete),
            'first_tier_count': sum(CITY_CATALOG[c]['tier'] == 1 for c in complete),
            'second_tier_count': sum(CITY_CATALOG[c]['tier'] == 2 for c in complete),
            'first_period': periods[0] if periods else None, 'latest_period': latest,
            'periods': periods, 'month_count': len(periods),
            'price_record_count': db.scalar(select(func.count()).select_from(PriceObservation).where(PriceObservation.city.in_(target))),
            'document_count': db.scalar(select(func.count()).select_from(SourceDocument)),
            'housing_cities': housing_cities, 'latest_sync': run_json(latest_run) if latest_run else None,
            'tier_source_url': TIER_SOURCE_URL,
            'methodology': '国家统计局价格指数；环比以上月=100，同比以上年同月=100。不是元/平方米。'}


@router.get('/cities')
def cities(db: Session = Depends(get_db)):
    rows = db.scalars(select(PriceObservation).where(PriceObservation.city.in_(list(CITY_CATALOG))).order_by(PriceObservation.period)).all()
    grouped = {}
    for row in rows:
        grouped.setdefault((row.city, row.house_type), []).append(row)
    data = []
    for city, meta in CITY_CATALOG.items():
        item = {'city': city, **meta}
        for kind in ['new', 'second_hand']:
            history = grouped.get((city, kind), [])
            last = history[-1] if history else None
            if history:
                year, month = map(int, last.period.split('-'))
                offset = year * 12 + month - 1 - 23
                start = max(history[0].period, f'{offset // 12:04d}-{offset % 12 + 1:02d}')
            else:
                start = None
            item[kind] = {'period': last.period if last else None,
                          'mom_change': round(last.mom_index - 100, 2) if last and last.mom_index is not None else None,
                          'yoy_change': round(last.yoy_index - 100, 2) if last and last.yoy_index is not None else None,
                          'source_id': last.source_id if last else None,
                          'sparkline': build_series(history, start, last.period, 'yoy_change') if history else []}
        data.append(item)
    return {'cities': data, 'tier_source_url': TIER_SOURCE_URL}


@router.get('/series')
def series(cities: str = '北京,上海,广州,深圳', house_type: HouseType = 'second_hand',
           metric: Metric = 'yoy_change', start: str | None = None, end: str | None = None,
           db: Session = Depends(get_db)):
    names = selected_cities(cities, 8)
    start, end = price_bounds(db, start, end)
    if start is None:
        return {'series': [], 'sources': [], 'start': None, 'end': None, 'metric': metric}
    rows = db.scalars(select(PriceObservation).where(PriceObservation.city.in_(names),
                     PriceObservation.house_type == house_type, PriceObservation.period >= start,
                     PriceObservation.period <= end).order_by(PriceObservation.period)).all()
    source_ids = {row.source_id for row in rows}
    docs = db.scalars(select(SourceDocument).where(SourceDocument.id.in_(source_ids))).all()
    return {'start': start, 'end': end, 'house_type': house_type, 'metric': metric,
            'unit': '指数' if metric == 'relative_index' else '%',
            'baseline_period': start if metric == 'relative_index' else None,
            'methodology': '相对指数以所选起始月=100，连乘其后各月官方环比指数；不是官方定基指数，存在四舍五入误差，断档后停止计算。' if metric == 'relative_index' else '官方指数减100，表示同比或环比变化百分比。',
            'series': [{'city': city, 'points': build_series([r for r in rows if r.city == city], start, end, metric)} for city in names],
            'sources': [document_json(doc) for doc in docs]}


@router.get('/observations')
def observations(period: str | None = None, cities: str | None = None, house_type: HouseType = 'second_hand', db: Session = Depends(get_db)):
    names = selected_cities(cities)
    period = period or db.scalar(select(func.max(PriceObservation.period)))
    if not period:
        return {'period': None, 'total': 0, 'items': []}
    try:
        validate_period(period)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    rows = db.execute(select(PriceObservation, SourceDocument).join(SourceDocument).where(
        PriceObservation.city.in_(names), PriceObservation.period == period, PriceObservation.house_type == house_type)).all()
    return {'period': period, 'total': len(rows), 'items': [
        {'city': row.city, 'tier': CITY_CATALOG[row.city]['tier'], 'house_type': row.house_type,
         'mom_index': row.mom_index, 'yoy_index': row.yoy_index,
         'mom_change': round(row.mom_index - 100, 2) if row.mom_index is not None else None,
         'yoy_change': round(row.yoy_index - 100, 2) if row.yoy_index is not None else None,
         'source': document_json(doc)} for row, doc in rows]}


@router.get('/housing')
def housing(city: str = '石家庄', frequency: Literal['month', 'year'] = 'month', db: Session = Depends(get_db)):
    if city not in CITY_CATALOG:
        raise HTTPException(422, '城市未登记')
    rows = db.execute(select(HousingObservation, SourceDocument).join(SourceDocument).where(
        HousingObservation.city == city, HousingObservation.frequency == frequency).order_by(HousingObservation.period)).all()
    return {'city': city, 'frequency': frequency, 'total': len(rows), 'items': [
        {'period': row.period, 'house_type': row.house_type, 'transaction_count': row.transaction_count,
         'area_sqm': row.area_sqm, 'scope': row.scope, 'note': row.note, 'source': document_json(doc)} for row, doc in rows]}


@router.get('/sources')
def sources(db: Session = Depends(get_db)):
    providers = [{'key': 'nbs', 'name': '国家统计局', 'city': '70城 / 一二线35城',
                  'url': 'https://www.stats.gov.cn/sj/zxfb/', 'adapter': True,
                  'note': '新建商品住宅及二手住宅价格环比、同比指数。'}] + LOCAL_SOURCES
    data = []
    for provider in providers:
        doc = db.scalar(select(SourceDocument).where(SourceDocument.provider == provider['key']).order_by(SourceDocument.fetched_at.desc()).limit(1))
        model = PriceObservation if provider['key'] == 'nbs' else HousingObservation
        count, earliest, latest = db.execute(select(func.count(model.id), func.min(model.period), func.max(model.period)).where(model.provider == provider['key'])).one()
        data.append({**provider, 'status': 'connected' if count else 'ready' if provider['adapter'] else 'unavailable',
                     'record_count': count, 'first_period': earliest, 'latest_period': latest,
                     'last_fetched_at': doc.fetched_at.isoformat() + 'Z' if doc else None})
    runs = db.scalars(select(SyncRun).order_by(SyncRun.id.desc()).limit(10)).all()
    return {'sources': data, 'runs': [run_json(run) for run in runs]}


@router.get('/documents')
def documents(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    count = db.scalar(select(func.count()).select_from(SourceDocument))
    rows = db.scalars(select(SourceDocument).order_by(SourceDocument.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {'total': count, 'page': page, 'page_size': page_size, 'items': [document_json(row) for row in rows]}


@router.get('/documents/{document_id}/snapshot')
def snapshot(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(SourceDocument, document_id)
    if not doc:
        raise HTTPException(404, '来源记录不存在')
    path = (settings.DATA_DIR / doc.snapshot_path).resolve()
    if not path.is_relative_to((settings.DATA_DIR / 'raw').resolve()) or not path.is_file():
        raise HTTPException(404, '原始快照不存在')
    # 附件下载，不在应用域名内执行源站HTML和脚本。
    return FileResponse(path, media_type='application/octet-stream', filename=f'{doc.provider}-{doc.sha256[:12]}.html')


@router.get('/export/prices')
def export_prices(cities: str | None = None, house_type: HouseType = 'second_hand', start: str | None = None,
                  end: str | None = None, db: Session = Depends(get_db)):
    names = selected_cities(cities)
    start, end = price_bounds(db, start, end)
    rows = db.execute(select(PriceObservation, SourceDocument).join(SourceDocument).where(
        PriceObservation.city.in_(names), PriceObservation.house_type == house_type,
        PriceObservation.period >= start, PriceObservation.period <= end).order_by(PriceObservation.city, PriceObservation.period)).all() if start else []
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(['城市', '月份', '住宅类型', '环比指数(上月=100)', '同比指数(上年同月=100)', '来源', '公告标题', '来源链接', '发布日期', '采集时间(UTC)', '网页SHA256'])
    for row, doc in rows:
        writer.writerow([row.city, row.period, '新房' if row.house_type == 'new' else '二手房', row.mom_index,
                         row.yoy_index, doc.provider, doc.title, doc.url, doc.published_at, doc.fetched_at.isoformat(), doc.sha256])
    return Response('\ufeff' + stream.getvalue(), media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': 'attachment; filename="official-price-indices.csv"'})


class SyncRequest(BaseModel):
    start_period: str = Field(default=settings.DEFAULT_START_PERIOD, pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    end_period: str = Field(default_factory=previous_month, pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    refresh: bool = False
    include_housing: bool = True


@router.post('/sync', status_code=202)
def start_sync(request: SyncRequest, background_tasks: BackgroundTasks):
    try:
        run_id = create_run(request.start_period, request.end_period)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except SyncAlreadyRunning as error:
        raise HTTPException(409, str(error)) from error
    background_tasks.add_task(run_sync, run_id, request.refresh, request.include_housing)
    return {'id': run_id, 'status': 'running'}


@router.get('/sync/{run_id}')
def sync_status(run_id: int, db: Session = Depends(get_db)):
    run = db.get(SyncRun, run_id)
    if not run:
        raise HTTPException(404, '同步任务不存在')
    return run_json(run)
