from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
engine = create_engine(settings.DATABASE_URL, connect_args={'check_same_thread': False, 'timeout': 30} if settings.DATABASE_URL.startswith('sqlite') else {})


if settings.DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def configure_sqlite(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA busy_timeout=30000')


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db


def init_db():
    from app.models.official import City, SchemaVersion
    from app.catalog import CITY_CATALOG
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.get(SchemaVersion, 1) is None:
            db.add(SchemaVersion(version=1))
        for city, details in CITY_CATALOG.items():
            if db.get(City, city) is None:
                db.add(City(name=city, **details))
        db.commit()
