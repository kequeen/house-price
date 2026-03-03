from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class RegionStats(Base):
    __tablename__ = "region_stats"

    id = Column(Integer, primary_key=True, index=True)
    
    region = Column(String(50), index=True, comment="区域")
    district = Column(String(50), index=True, comment="片区/板块")
    
    year = Column(Integer, index=True, comment="年份")
    month = Column(Integer, index=True, comment="月份")
    
    total_transactions = Column(Integer, default=0, comment="成交总量")
    total_area = Column(Float, default=0, comment="成交总面积")
    total_amount = Column(Float, default=0, comment="成交总金额")
    
    avg_price = Column(Float, comment="平均单价")
    avg_unit_price = Column(Float, comment="平均成交价")
    
    max_price = Column(Float, comment="最高单价")
    min_price = Column(Float, comment="最低单价")
    
    data_source = Column(String(20), comment="数据来源")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NationalPriceStats(Base):
    __tablename__ = "national_price_stats"

    id = Column(Integer, primary_key=True, index=True)
    
    year = Column(Integer, unique=True, index=True, comment="年份")
    
    new_commercial_avg_price = Column(Float, comment="新建商品房平均销售价格(元/平方米)")
    residential_avg_price = Column(Float, comment="住宅商品房平均销售价格(元/平方米)")
    office_avg_price = Column(Float, comment="办公楼商品房平均销售价格(元/平方米)")
    commercial_building_avg_price = Column(Float, comment="商业营业用房平均销售价格(元/平方米)")
    other_avg_price = Column(Float, comment="其他商品房平均销售价格(元/平方米)")
    
    data_source = Column(String(50), default="国家统计局", comment="数据来源")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CityMonthlyStats(Base):
    __tablename__ = "city_monthly_stats"

    id = Column(Integer, primary_key=True, index=True)
    
    city = Column(String(50), index=True, comment="城市")
    year = Column(Integer, index=True, comment="年份")
    month = Column(Integer, index=True, comment="月份")
    
    total_transactions = Column(Integer, default=0, comment="成交总量")
    total_area = Column(Float, default=0, comment="成交总面积")
    total_amount = Column(Float, default=0, comment="成交总金额")
    
    avg_price = Column(Float, comment="平均单价")
    
    new_house_count = Column(Integer, default=0, comment="新房成交量")
    second_hand_count = Column(Integer, default=0, comment="二手房成交量")
    
    data_source = Column(String(20), comment="数据来源")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
