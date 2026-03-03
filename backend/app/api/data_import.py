from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import io

from app.database import get_db
from app.models.transaction import Transaction
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("/import/csv", response_model=ApiResponse)
async def import_csv(
    file: UploadFile = File(...),
    data_source: str = "government",
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")
    
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))
    
    required_columns = ['region']
    for col in required_columns:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"缺少必需列: {col}")
    
    imported_count = 0
    
    for _, row in df.iterrows():
        try:
            transaction_date = None
            year = None
            month = None
            
            if 'transaction_date' in df.columns and pd.notna(row.get('transaction_date')):
                transaction_date = pd.to_datetime(row['transaction_date'])
                year = transaction_date.year
                month = transaction_date.month
            
            transaction = Transaction(
                region=str(row.get('region', '')),
                district=str(row.get('district', '')) if pd.notna(row.get('district')) else None,
                community=str(row.get('community', '')) if pd.notna(row.get('community')) else None,
                transaction_date=transaction_date,
                year=year,
                month=month,
                price=float(row['price']) if pd.notna(row.get('price')) else None,
                unit_price=float(row['unit_price']) if pd.notna(row.get('unit_price')) else None,
                area=float(row['area']) if pd.notna(row.get('area')) else None,
                property_type=str(row.get('property_type', '')) if pd.notna(row.get('property_type')) else None,
                floor=str(row.get('floor', '')) if pd.notna(row.get('floor')) else None,
                orientation=str(row.get('orientation', '')) if pd.notna(row.get('orientation')) else None,
                decoration=str(row.get('decoration', '')) if pd.notna(row.get('decoration')) else None,
                bedrooms=int(row['bedrooms']) if pd.notna(row.get('bedrooms')) else None,
                living_rooms=int(row['living_rooms']) if pd.notna(row.get('living_rooms')) else None,
                data_source=data_source
            )
            db.add(transaction)
            imported_count += 1
        except Exception as e:
            continue
    
    db.commit()
    
    return ApiResponse(
        message=f"成功导入 {imported_count} 条数据",
        data={"imported_count": imported_count}
    )


@router.post("/import/excel", response_model=ApiResponse)
async def import_excel(
    file: UploadFile = File(...),
    data_source: str = "government",
    db: Session = Depends(get_db)
):
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")
    
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    required_columns = ['region']
    for col in required_columns:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"缺少必需列: {col}")
    
    imported_count = 0
    
    for _, row in df.iterrows():
        try:
            transaction_date = None
            year = None
            month = None
            
            if 'transaction_date' in df.columns and pd.notna(row.get('transaction_date')):
                transaction_date = pd.to_datetime(row['transaction_date'])
                year = transaction_date.year
                month = transaction_date.month
            
            transaction = Transaction(
                region=str(row.get('region', '')),
                district=str(row.get('district', '')) if pd.notna(row.get('district')) else None,
                community=str(row.get('community', '')) if pd.notna(row.get('community')) else None,
                transaction_date=transaction_date,
                year=year,
                month=month,
                price=float(row['price']) if pd.notna(row.get('price')) else None,
                unit_price=float(row['unit_price']) if pd.notna(row.get('unit_price')) else None,
                area=float(row['area']) if pd.notna(row.get('area')) else None,
                property_type=str(row.get('property_type', '')) if pd.notna(row.get('property_type')) else None,
                floor=str(row.get('floor', '')) if pd.notna(row.get('floor')) else None,
                orientation=str(row.get('orientation', '')) if pd.notna(row.get('orientation')) else None,
                decoration=str(row.get('decoration', '')) if pd.notna(row.get('decoration')) else None,
                bedrooms=int(row['bedrooms']) if pd.notna(row.get('bedrooms')) else None,
                living_rooms=int(row['living_rooms']) if pd.notna(row.get('living_rooms')) else None,
                data_source=data_source
            )
            db.add(transaction)
            imported_count += 1
        except Exception as e:
            continue
    
    db.commit()
    
    return ApiResponse(
        message=f"成功导入 {imported_count} 条数据",
        data={"imported_count": imported_count}
    )


@router.get("/template")
def get_import_template():
    template = {
        "columns": [
            {"name": "region", "description": "区域（必填）", "example": "朝阳区"},
            {"name": "district", "description": "片区/板块", "example": "望京"},
            {"name": "community", "description": "小区名称", "example": "望京花园"},
            {"name": "transaction_date", "description": "成交日期", "example": "2024-01-15"},
            {"name": "price", "description": "成交总价(万元)", "example": 500},
            {"name": "unit_price", "description": "单价(元/平米)", "example": 50000},
            {"name": "area", "description": "面积(平米)", "example": 100},
            {"name": "property_type", "description": "物业类型", "example": "住宅"},
            {"name": "floor", "description": "楼层", "example": "中层/15层"},
            {"name": "orientation", "description": "朝向", "example": "南北"},
            {"name": "decoration", "description": "装修情况", "example": "精装"},
            {"name": "bedrooms", "description": "卧室数量", "example": 3},
            {"name": "living_rooms", "description": "客厅数量", "example": 2}
        ]
    }
    return template
