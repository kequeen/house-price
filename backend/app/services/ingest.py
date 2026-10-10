from sqlalchemy import select
from app.catalog import CITY_CATALOG
from app.models.official import City, HousingObservation, PriceObservation, SourceDocument


def source_document(db, page, parsed, provider, parser_version):
    existing = db.scalar(select(SourceDocument).where(SourceDocument.url == page.url, SourceDocument.sha256 == page.sha256))
    if existing:
        return existing
    document = SourceDocument(provider=provider, title=parsed['title'], url=page.url,
                              sha256=page.sha256, snapshot_path=page.snapshot_path,
                              fetched_at=page.fetched_at, published_at=parsed['published_at'],
                              parser_version=parser_version)
    db.add(document)
    db.flush()
    return document


def ingest_prices(db, page, parsed, parser_version):
    source = source_document(db, page, parsed, 'nbs', parser_version)
    changed = 0
    for item in parsed['records']:
        city = item['city']
        if db.get(City, city) is None:
            db.add(City(name=city, **CITY_CATALOG.get(city, {'tier': 3, 'province': None})))
            db.flush()
        existing = db.scalar(select(PriceObservation).where(
            PriceObservation.city == city, PriceObservation.period == item['period'],
            PriceObservation.house_type == item['house_type'], PriceObservation.provider == 'nbs'))
        if existing:
            if existing.source_id != source.id or existing.mom_index != item['mom_index'] or existing.yoy_index != item['yoy_index']:
                existing.source_id = source.id
                existing.mom_index, existing.yoy_index = item['mom_index'], item['yoy_index']
                changed += 1
        else:
            db.add(PriceObservation(**item, source_id=source.id))
            changed += 1
    db.commit()
    return changed


def ingest_housing(db, page, parsed, provider, parser_version):
    source = source_document(db, page, parsed, provider, parser_version)
    changed = 0
    for item in parsed['records']:
        existing = db.scalar(select(HousingObservation).where(*[
            getattr(HousingObservation, key) == item[key]
            for key in ['city', 'period', 'frequency', 'house_type', 'scope', 'provider']]))
        if existing:
            if existing.source_id != source.id or existing.transaction_count != item['transaction_count'] or existing.area_sqm != item['area_sqm']:
                existing.source_id = source.id
                existing.transaction_count, existing.area_sqm = item['transaction_count'], item['area_sqm']
                existing.note = item['note']
                changed += 1
        else:
            db.add(HousingObservation(**item, source_id=source.id))
            changed += 1
    db.commit()
    return changed
