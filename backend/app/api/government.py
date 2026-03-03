from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional, List

from app.database import get_db
from app.models.region import CityMonthlyStats, NationalPriceStats
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/government", tags=["government"])


@router.get("/stats/cities")
def get_city_stats(
    year: Optional[int] = None,
    month: Optional[int] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CityMonthlyStats)
    
    if year:
        query = query.filter(CityMonthlyStats.year == year)
    if month:
        query = query.filter(CityMonthlyStats.month == month)
    if city:
        query = query.filter(CityMonthlyStats.city == city)
    
    results = query.order_by(CityMonthlyStats.year.desc(), CityMonthlyStats.month.desc()).limit(100).all()
    
    return {
        "total": len(results),
        "items": [{
            "id": r.id,
            "city": r.city,
            "year": r.year,
            "month": r.month,
            "avg_price": r.avg_price,
            "total_transactions": r.total_transactions,
            "total_area": r.total_area,
            "total_amount": r.total_amount,
            "new_house_count": r.new_house_count,
            "second_hand_count": r.second_hand_count,
            "data_source": r.data_source
        } for r in results]
    }


@router.get("/stats/compare")
def get_city_compare(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    results = db.query(CityMonthlyStats).filter(
        CityMonthlyStats.year == year,
        CityMonthlyStats.month == month
    ).order_by(CityMonthlyStats.avg_price.desc()).all()
    
    return {
        "year": year,
        "month": month,
        "cities": [{
            "city": r.city,
            "avg_price": r.avg_price,
            "total_transactions": r.total_transactions,
            "new_house_count": r.new_house_count,
            "second_hand_count": r.second_hand_count
        } for r in results]
    }


@router.get("/trend/{city}")
def get_city_trend(
    city: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CityMonthlyStats).filter(CityMonthlyStats.city == city)
    
    if start_year:
        query = query.filter(CityMonthlyStats.year >= start_year)
    if end_year:
        query = query.filter(CityMonthlyStats.year <= end_year)
    
    results = query.order_by(CityMonthlyStats.year, CityMonthlyStats.month).all()
    
    return {
        "city": city,
        "data": [{
            "date": f"{r.year}-{r.month:02d}",
            "avg_price": r.avg_price,
            "total_transactions": r.total_transactions,
            "new_house_count": r.new_house_count,
            "second_hand_count": r.second_hand_count
        } for r in results]
    }


@router.get("/rankings")
def get_city_rankings(
    year: int,
    month: int,
    order_by: str = Query("avg_price", regex="^(avg_price|total_transactions|total_amount)$"),
    limit: int = Query(20, ge=5, le=70),
    db: Session = Depends(get_db)
):
    results = db.query(CityMonthlyStats).filter(
        CityMonthlyStats.year == year,
        CityMonthlyStats.month == month
    ).order_by(getattr(CityMonthlyStats, order_by).desc()).limit(limit).all()
    
    return {
        "year": year,
        "month": month,
        "order_by": order_by,
        "rankings": [{
            "rank": i + 1,
            "city": r.city,
            "avg_price": r.avg_price,
            "total_transactions": r.total_transactions,
            "total_amount": r.total_amount
        } for i, r in enumerate(results)]
    }


@router.get("/cities/list")
def get_available_cities(db: Session = Depends(get_db)):
    results = db.query(CityMonthlyStats.city).distinct().all()
    return {"cities": [r.city for r in results if r.city]}


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    latest = db.query(CityMonthlyStats).order_by(
        CityMonthlyStats.year.desc(),
        CityMonthlyStats.month.desc()
    ).first()
    
    if not latest:
        return {"message": "暂无数据"}
    
    city_count = db.query(CityMonthlyStats.city).filter(
        CityMonthlyStats.year == latest.year,
        CityMonthlyStats.month == latest.month
    ).count()
    
    total_stats = db.query(
        func.sum(CityMonthlyStats.total_transactions).label('total'),
        func.sum(CityMonthlyStats.total_amount).label('amount'),
        func.sum(CityMonthlyStats.total_area).label('area')
    ).filter(
        CityMonthlyStats.year == latest.year,
        CityMonthlyStats.month == latest.month
    ).first()
    
    total_transactions = total_stats.total or 0
    total_amount = total_stats.amount or 0
    total_area = total_stats.area or 0
    
    if total_area > 0:
        weighted_avg_price = round(total_amount * 10000 / total_area, 0)
    else:
        weighted_avg_price = 0
    
    return {
        "year": latest.year,
        "month": latest.month,
        "city_count": city_count,
        "total_transactions": total_transactions,
        "total_amount": total_amount,
        "total_area": total_area,
        "avg_price": weighted_avg_price,
        "calculation_method": "成交金额 / 成交面积 (加权平均)"
    }


@router.get("/provincial")
def get_provincial_stats(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    province_mapping = {
        '北京': '北京', '天津': '天津', '石家庄': '河北', '唐山': '河北', '秦皇岛': '河北',
        '太原': '山西', '大同': '山西', '呼和浩特': '内蒙古', '包头': '内蒙古',
        '沈阳': '辽宁', '大连': '辽宁', '长春': '吉林', '哈尔滨': '黑龙江',
        '上海': '上海', '南京': '江苏', '苏州': '江苏', '无锡': '江苏', '常州': '江苏',
        '杭州': '浙江', '宁波': '浙江', '温州': '浙江', '合肥': '安徽', '福州': '福建',
        '厦门': '福建', '南昌': '江西', '济南': '山东', '青岛': '山东', '郑州': '河南',
        '武汉': '湖北', '长沙': '湖南', '广州': '广东', '深圳': '广东', '东莞': '广东',
        '南宁': '广西', '海口': '海南', '三亚': '海南', '重庆': '重庆', '成都': '四川',
        '贵阳': '贵州', '昆明': '云南', '拉萨': '西藏', '西安': '陕西', '兰州': '甘肃',
        '西宁': '青海', '银川': '宁夏', '乌鲁木齐': '新疆'
    }
    
    results = db.query(CityMonthlyStats).filter(
        CityMonthlyStats.year == year,
        CityMonthlyStats.month == month
    ).all()
    
    province_data = {}
    for r in results:
        province = province_mapping.get(r.city, '其他')
        if province not in province_data:
            province_data[province] = {
                'province': province,
                'total_transactions': 0,
                'total_amount': 0,
                'total_area': 0,
                'city_count': 0
            }
        province_data[province]['total_transactions'] += r.total_transactions or 0
        province_data[province]['total_amount'] += r.total_amount or 0
        province_data[province]['total_area'] += r.total_area or 0
        province_data[province]['city_count'] += 1
    
    for p in province_data.values():
        if p['total_area'] > 0:
            p['avg_price'] = round(p['total_amount'] * 10000 / p['total_area'], 0)
        else:
            p['avg_price'] = 0
    
    return {
        "year": year,
        "month": month,
        "provinces": sorted(province_data.values(), key=lambda x: x['avg_price'], reverse=True)
    }


@router.get("/national/prices")
def get_national_prices(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(NationalPriceStats)
    
    if start_year:
        query = query.filter(NationalPriceStats.year >= start_year)
    if end_year:
        query = query.filter(NationalPriceStats.year <= end_year)
    
    results = query.order_by(NationalPriceStats.year).all()
    
    data = []
    prev_price = None
    for r in results:
        item = {
            "year": r.year,
            "new_commercial_avg_price": r.new_commercial_avg_price,
            "residential_avg_price": r.residential_avg_price,
            "office_avg_price": r.office_avg_price,
            "commercial_building_avg_price": r.commercial_building_avg_price,
            "other_avg_price": r.other_avg_price,
            "data_source": r.data_source
        }
        
        if prev_price is not None and r.new_commercial_avg_price:
            item["yoy_change"] = round(
                (r.new_commercial_avg_price - prev_price) / prev_price * 100, 1
            )
        else:
            item["yoy_change"] = None
        
        if r.new_commercial_avg_price:
            prev_price = r.new_commercial_avg_price
        
        data.append(item)
    
    return {
        "total": len(data),
        "data": data
    }


@router.get("/national/prices/{year}")
def get_national_price_by_year(
    year: int,
    db: Session = Depends(get_db)
):
    result = db.query(NationalPriceStats).filter(
        NationalPriceStats.year == year
    ).first()
    
    if not result:
        return {"message": f"暂无 {year} 年数据"}
    
    prev_year = db.query(NationalPriceStats).filter(
        NationalPriceStats.year == year - 1
    ).first()
    
    data = {
        "year": result.year,
        "new_commercial_avg_price": result.new_commercial_avg_price,
        "residential_avg_price": result.residential_avg_price,
        "office_avg_price": result.office_avg_price,
        "commercial_building_avg_price": result.commercial_building_avg_price,
        "other_avg_price": result.other_avg_price,
        "data_source": result.data_source
    }
    
    if prev_year and prev_year.new_commercial_avg_price and result.new_commercial_avg_price:
        data["yoy_change"] = round(
            (result.new_commercial_avg_price - prev_year.new_commercial_avg_price) 
            / prev_year.new_commercial_avg_price * 100, 1
        )
    
    return data


@router.get("/national/summary")
def get_national_summary(db: Session = Depends(get_db)):
    latest = db.query(NationalPriceStats).order_by(
        NationalPriceStats.year.desc()
    ).first()
    
    if not latest:
        return {"message": "暂无数据"}
    
    first = db.query(NationalPriceStats).order_by(
        NationalPriceStats.year
    ).first()
    
    years = db.query(NationalPriceStats.year).order_by(
        NationalPriceStats.year
    ).all()
    year_count = len(years)
    
    min_year = years[0][0] if years else None
    max_year = years[-1][0] if years else None
    
    peak = db.query(NationalPriceStats).order_by(
        NationalPriceStats.new_commercial_avg_price.desc()
    ).first()
    
    return {
        "latest_year": latest.year,
        "latest_price": latest.new_commercial_avg_price,
        "latest_residential_price": latest.residential_avg_price,
        "peak_year": peak.year if peak else None,
        "peak_price": peak.new_commercial_avg_price if peak else None,
        "year_range": f"{min_year}-{max_year}" if min_year and max_year else None,
        "year_count": year_count,
        "data_source": "国家统计局"
    }
