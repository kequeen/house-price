from datetime import timedelta
import json
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.config import settings
from app.database import SessionLocal
from app.models.official import SyncRun, utcnow
from app.collectors.http import OfficialClient
from app.collectors import nbs, housing
from app.services.ingest import ingest_prices, ingest_housing


class SyncAlreadyRunning(Exception):
    pass


def create_run(start, end):
    nbs.validate_period(start)
    nbs.validate_period(end)
    if start > end:
        raise ValueError('起始月份不能晚于结束月份')
    if int(end[:4]) * 12 + int(end[5:]) - int(start[:4]) * 12 - int(start[5:]) > 60:
        raise ValueError('单次同步最多61个月，更长历史请分批获取')
    with SessionLocal() as db:
        # 崩溃后通过持久化心跳恢复；不会把仍在其他进程运行的CLI任务取消。
        stale = db.scalars(select(SyncRun).where(SyncRun.status == 'running', SyncRun.heartbeat_at < utcnow() - timedelta(minutes=30))).all()
        for run in stale:
            run.status, run.finished_at, run.progress = 'failed', utcnow(), '任务中断，已释放同步锁'
        db.commit()
        run = SyncRun(start_period=start, end_period=end)
        db.add(run)
        try:
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise SyncAlreadyRunning('已有同步任务正在运行') from error
        return run.id


def update_run(run_id, **values):
    with SessionLocal() as db:
        run = db.get(SyncRun, run_id)
        for key, value in values.items():
            setattr(run, key, value)
        run.heartbeat_at = utcnow()
        db.commit()


def run_sync(run_id, refresh=False, include_housing=True):
    with SessionLocal() as db:
        run = db.get(SyncRun, run_id)
        start, end = run.start_period, run.end_period
    client = OfficialClient()
    errors, price_count, housing_count = [], 0, 0

    def progress(message):
        update_run(run_id, progress=message, price_records=price_count,
                   housing_records=housing_count, errors_json=json.dumps(errors, ensure_ascii=False))
        print(message, flush=True)

    def failure(provider, period, error):
        errors.append({'provider': provider, 'period': period, 'message': str(error)[:500]})

    try:
        releases = nbs.discover_releases(client, start, end, progress, refresh=refresh)
        if not releases:
            raise ValueError('请求范围内未找到70城官方公告')
        latest = max(releases)
        for period in nbs.month_range(start, latest):
            if period not in releases:
                failure('nbs', period, '未找到该月官方公告；保留缺失，不填零')
                continue
            progress(f'国家统计局 · {period} · 新房与二手房')
            try:
                page = client.fetch(releases[period], refresh=refresh)
                parsed = nbs.parse_nbs(page.html, period)
                with SessionLocal() as db:
                    price_count += ingest_prices(db, page, parsed, nbs.PARSER_VERSION)
            except Exception as error:
                failure('nbs', period, error)
        if include_housing:
            progress('北京市住建委 · 官方住宅交易统计')
            try:
                page = client.fetch(housing.BEIJING_URL, refresh=refresh, max_age=86400)
                parsed = housing.parse_beijing(page.html)
                # 北京年度表是独立年度口径，保留其原始期间，月表限制在所选范围内。
                parsed['records'] = [r for r in parsed['records'] if (r['frequency'] == 'year' and start[:4] <= r['period'] <= end[:4]) or (r['frequency'] == 'month' and start <= r['period'] <= end)]
                with SessionLocal() as db:
                    housing_count += ingest_housing(db, page, parsed, 'beijing', housing.PARSER_VERSION)
            except Exception as error:
                failure('beijing', None, error)
            for period in nbs.month_range(start, end):
                progress(f'石家庄市住建局 · {period} · 月度住宅网签')
                try:
                    page = client.fetch(housing.SJZ_URL.format(period=period), refresh=refresh, max_age=86400 if period >= latest else None)
                    parsed = housing.parse_shijiazhuang(page.html, period)
                    with SessionLocal() as db:
                        housing_count += ingest_housing(db, page, parsed, 'shijiazhuang', housing.PARSER_VERSION)
                except Exception as error:
                    failure('shijiazhuang', period, error)
        status = 'partial' if errors else 'succeeded'
        if not price_count:
            with SessionLocal() as db:
                from app.models.official import PriceObservation
                has_prices = db.scalar(select(PriceObservation.id).where(PriceObservation.period >= start, PriceObservation.period <= end).limit(1))
            if not has_prices:
                status = 'failed'
        update_run(run_id, status=status, finished_at=utcnow(),
                   progress=f'同步结束：更新{price_count}条价格指数、{housing_count}条成交统计',
                   price_records=price_count, housing_records=housing_count,
                   errors_json=json.dumps(errors, ensure_ascii=False))
    except Exception as error:
        failure('sync', None, error)
        update_run(run_id, status='failed', finished_at=utcnow(), progress='同步失败，已有官方数据保留',
                   errors_json=json.dumps(errors, ensure_ascii=False), price_records=price_count, housing_records=housing_count)
    finally:
        client.close()
