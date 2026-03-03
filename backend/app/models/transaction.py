from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class DataSource(enum.Enum):
    LIANJIA = "lianjia"
    GOVERNMENT = "government"
    OTHER = "other"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    region = Column(String(50), index=True, comment="区域")
    district = Column(String(50), index=True, comment="片区/板块")
    community = Column(String(100), comment="小区名称")
    
    transaction_date = Column(DateTime, index=True, comment="成交日期")
    year = Column(Integer, index=True, comment="年份")
    month = Column(Integer, index=True, comment="月份")
    
    price = Column(Float, comment="成交总价(万元)")
    unit_price = Column(Float, comment="单价(元/平米)")
    area = Column(Float, comment="面积(平米)")
    
    property_type = Column(String(50), comment="物业类型")
    floor = Column(String(50), comment="楼层")
    orientation = Column(String(50), comment="朝向")
    decoration = Column(String(50), comment="装修情况")
    
    bedrooms = Column(Integer, comment="卧室数量")
    living_rooms = Column(Integer, comment="客厅数量")
    
    data_source = Column(String(20), default=DataSource.LIANJIA.value, comment="数据来源")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
