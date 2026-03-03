from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Optional, List

from app.database import get_db
from app.models.transaction import Transaction
from app.models.region import RegionStats, CityMonthlyStats
from app.schemas.transaction import (
    TransactionResponse, TransactionFilter, RegionStatsResponse,
    MonthlyStatsResponse, PriceTrendItem, VolumeTrendItem, RegionCompareItem
)
from app.schemas.common import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=PaginatedResponse)
def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    region: Optional[str] = None,
    district: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    data_source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Transaction)
    
    if region:
        query = query.filter(Transaction.region == region)
    if district:
        query = query.filter(Transaction.district == district)
    if year:
        query = query.filter(Transaction.year == year)
    if month:
        query = query.filter(Transaction.month == month)
    if data_source:
        query = query.filter(Transaction.data_source == data_source)
    
    total = query.count()
    items = query.order_by(Transaction.transaction_date.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[{
            "id": item.id,
            "region": item.region,
            "district": item.district,
            "community": item.community,
            "transaction_date": item.transaction_date.isoformat() if item.transaction_date else None,
            "year": item.year,
            "month": item.month,
            "price": item.price,
            "unit_price": item.unit_price,
            "area": item.area,
            "property_type": item.property_type,
            "data_source": item.data_source
        } for item in items]
    )


@router.get("/stats/monthly", response_model=List[MonthlyStatsResponse])
def get_monthly_stats(
    year: Optional[int] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Transaction.year,
        Transaction.month,
        func.count(Transaction.id).label('total_transactions'),
        func.sum(Transaction.area).label('total_area'),
        func.sum(Transaction.price).label('total_amount'),
        func.avg(Transaction.unit_price).label('avg_price')
    ).group_by(Transaction.year, Transaction.month)
    
    if year:
        query = query.filter(Transaction.year == year)
    if region:
        query = query.filter(Transaction.region == region)
    
    results = query.order_by(Transaction.year, Transaction.month).all()
    
    return [
        MonthlyStatsResponse(
            year=r.year,
            month=r.month,
            total_transactions=r.total_transactions,
            total_area=r.total_area or 0,
            total_amount=r.total_amount or 0,
            avg_price=r.avg_price
        ) for r in results
    ]


@router.get("/stats/regions", response_model=List[RegionCompareItem])
def get_region_stats(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Transaction.region,
        func.avg(Transaction.unit_price).label('avg_price'),
        func.count(Transaction.id).label('transaction_count'),
        func.sum(Transaction.price).label('total_amount')
    ).group_by(Transaction.region)
    
    if year:
        query = query.filter(Transaction.year == year)
    if month:
        query = query.filter(Transaction.month == month)
    
    results = query.all()
    
    return [
        RegionCompareItem(
            region=r.region,
            avg_price=r.avg_price or 0,
            transaction_count=r.transaction_count,
            total_amount=r.total_amount or 0
        ) for r in results
    ]


@router.get("/trends/price", response_model=List[PriceTrendItem])
def get_price_trend(
    region: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Transaction.year,
        Transaction.month,
        func.avg(Transaction.unit_price).label('avg_price'),
        func.count(Transaction.id).label('transaction_count')
    ).group_by(Transaction.year, Transaction.month)
    
    if region:
        query = query.filter(Transaction.region == region)
    if start_year:
        query = query.filter(Transaction.year >= start_year)
    if end_year:
        query = query.filter(Transaction.year <= end_year)
    
    results = query.order_by(Transaction.year, Transaction.month).all()
    
    return [
        PriceTrendItem(
            date=f"{r.year}-{r.month:02d}",
            avg_price=r.avg_price or 0,
            transaction_count=r.transaction_count
        ) for r in results
    ]


@router.get("/trends/volume", response_model=List[VolumeTrendItem])
def get_volume_trend(
    region: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Transaction.year,
        Transaction.month,
        func.count(Transaction.id).label('volume'),
        func.sum(Transaction.price).label('total_amount')
    ).group_by(Transaction.year, Transaction.month)
    
    if region:
        query = query.filter(Transaction.region == region)
    if start_year:
        query = query.filter(Transaction.year >= start_year)
    if end_year:
        query = query.filter(Transaction.year <= end_year)
    
    results = query.order_by(Transaction.year, Transaction.month).all()
    
    return [
        VolumeTrendItem(
            date=f"{r.year}-{r.month:02d}",
            volume=r.volume,
            total_amount=r.total_amount or 0
        ) for r in results
    ]


@router.get("/regions/list")
def get_regions(db: Session = Depends(get_db)):
    results = db.query(Transaction.region).distinct().all()
    return {"regions": [r.region for r in results if r.region]}


@router.get("/districts/{region}")
def get_districts(region: str, db: Session = Depends(get_db)):
    results = db.query(Transaction.district).filter(
        Transaction.region == region
    ).distinct().all()
    return {"districts": [r.district for r in results if r.district]}


@router.get("/years")
def get_years(db: Session = Depends(get_db)):
    results = db.query(Transaction.year).distinct().order_by(Transaction.year.desc()).all()
    return {"years": [r.year for r in results if r.year]}
