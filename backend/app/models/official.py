from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index, text
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SchemaVersion(Base):
    __tablename__ = 'schema_versions'
    version = Column(Integer, primary_key=True)
    applied_at = Column(DateTime, nullable=False, default=utcnow)


class City(Base):
    __tablename__ = 'cities'
    name = Column(String(20), primary_key=True)
    tier = Column(Integer, nullable=False)
    province = Column(String(20), nullable=True)


class SourceDocument(Base):
    __tablename__ = 'source_documents'
    __table_args__ = (UniqueConstraint('url', 'sha256'),)
    id = Column(Integer, primary_key=True)
    provider = Column(String(40), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    sha256 = Column(String(64), nullable=False)
    snapshot_path = Column(String(200), nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=utcnow)
    published_at = Column(String(20), nullable=True)
    parser_version = Column(String(30), nullable=False)


class PriceObservation(Base):
    __tablename__ = 'price_observations'
    __table_args__ = (
        UniqueConstraint('city', 'period', 'house_type', 'provider'),
        CheckConstraint("house_type IN ('new', 'second_hand')"),
        CheckConstraint('mom_index IS NULL OR mom_index > 0'),
        CheckConstraint('yoy_index IS NULL OR yoy_index > 0'),
        Index('ix_price_period_city', 'period', 'city'),
    )
    id = Column(Integer, primary_key=True)
    city = Column(String(20), ForeignKey('cities.name'), nullable=False)
    period = Column(String(7), nullable=False)
    house_type = Column(String(20), nullable=False)
    provider = Column(String(40), nullable=False, default='nbs')
    mom_index = Column(Float, nullable=True)
    yoy_index = Column(Float, nullable=True)
    source_id = Column(Integer, ForeignKey('source_documents.id'), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class HousingObservation(Base):
    __tablename__ = 'housing_observations'
    __table_args__ = (
        UniqueConstraint('city', 'period', 'frequency', 'house_type', 'scope', 'provider'),
        CheckConstraint("frequency IN ('month', 'year')"),
        CheckConstraint("house_type IN ('new', 'second_hand')"),
        CheckConstraint('transaction_count IS NULL OR transaction_count >= 0'),
        CheckConstraint('area_sqm IS NULL OR area_sqm >= 0'),
    )
    id = Column(Integer, primary_key=True)
    city = Column(String(20), ForeignKey('cities.name'), nullable=False)
    period = Column(String(7), nullable=False)
    frequency = Column(String(10), nullable=False)
    house_type = Column(String(20), nullable=False)
    scope = Column(String(200), nullable=False)
    provider = Column(String(40), nullable=False)
    transaction_count = Column(Float, nullable=True)
    area_sqm = Column(Float, nullable=True)
    source_id = Column(Integer, ForeignKey('source_documents.id'), nullable=False)
    note = Column(String(300), nullable=True)


class SyncRun(Base):
    __tablename__ = 'sync_runs'
    __table_args__ = (Index('one_active_sync', 'status', unique=True, sqlite_where=text("status = 'running'")),)
    id = Column(Integer, primary_key=True)
    status = Column(String(20), nullable=False, default='running')
    started_at = Column(DateTime, nullable=False, default=utcnow)
    heartbeat_at = Column(DateTime, nullable=False, default=utcnow)
    finished_at = Column(DateTime, nullable=True)
    start_period = Column(String(7), nullable=False)
    end_period = Column(String(7), nullable=False)
    progress = Column(String(300), nullable=False, default='等待采集')
    price_records = Column(Integer, nullable=False, default=0)
    housing_records = Column(Integer, nullable=False, default=0)
    errors_json = Column(String, nullable=False, default='[]')
