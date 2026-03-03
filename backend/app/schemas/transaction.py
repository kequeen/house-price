from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TransactionBase(BaseModel):
    region: str
    district: Optional[str] = None
    community: Optional[str] = None
    transaction_date: Optional[datetime] = None
    year: Optional[int] = None
    month: Optional[int] = None
    price: Optional[float] = None
    unit_price: Optional[float] = None
    area: Optional[float] = None
    property_type: Optional[str] = None
    floor: Optional[str] = None
    orientation: Optional[str] = None
    decoration: Optional[str] = None
    bedrooms: Optional[int] = None
    living_rooms: Optional[int] = None
    data_source: str = "lianjia"


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionFilter(BaseModel):
    region: Optional[str] = None
    district: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    data_source: Optional[str] = None


class RegionStatsResponse(BaseModel):
    region: str
    district: Optional[str] = None
    year: int
    month: int
    total_transactions: int
    total_area: float
    total_amount: float
    avg_price: Optional[float] = None
    avg_unit_price: Optional[float] = None
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    data_source: Optional[str] = None

    class Config:
        from_attributes = True


class MonthlyStatsResponse(BaseModel):
    year: int
    month: int
    total_transactions: int
    total_area: float
    total_amount: float
    avg_price: Optional[float] = None
    new_house_count: Optional[int] = None
    second_hand_count: Optional[int] = None

    class Config:
        from_attributes = True


class PriceTrendItem(BaseModel):
    date: str
    avg_price: float
    transaction_count: int


class VolumeTrendItem(BaseModel):
    date: str
    volume: int
    total_amount: float


class RegionCompareItem(BaseModel):
    region: str
    avg_price: float
    transaction_count: int
    total_amount: float
