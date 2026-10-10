"""从已登记的官方网页发现公告、校验表格并同步。支持离线缓存与修订重取。"""
import argparse
import json
from app.config import settings
from app.database import init_db, SessionLocal
from app.collectors.nbs import previous_month
from app.models.official import SyncRun
from app.services.sync import create_run, run_sync


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default=settings.DEFAULT_START_PERIOD)
    parser.add_argument('--end', default=previous_month())
    parser.add_argument('--refresh', action='store_true', help='重新读取网页，保留修订前后快照')
    parser.add_argument('--price-only', action='store_true', help='只同步国家统计局价格指数')
    args = parser.parse_args()
    init_db()
    run_id = create_run(args.start, args.end)
    run_sync(run_id, refresh=args.refresh, include_housing=not args.price_only)
    with SessionLocal() as db:
        run = db.get(SyncRun, run_id)
        print(json.dumps({'run_id': run_id, 'status': run.status, 'price_records': run.price_records,
                          'housing_records': run.housing_records, 'errors': json.loads(run.errors_json)}, ensure_ascii=False, indent=2))
        return 0 if run.status == 'succeeded' else 2 if run.status == 'partial' else 1


if __name__ == '__main__':
    raise SystemExit(main())
