from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.transaction import Transaction
from app.crawlers.lianjia import crawl_lianjia_data
from app.crawlers.shanghai_housing import crawl_shanghai_housing
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/crawler", tags=["crawler"])


crawler_status = {
    "is_running": False,
    "last_run": None,
    "total_crawled": 0,
    "current_region": None
}

government_crawler_status = {
    "is_running": False,
    "last_run": None,
    "city": None,
    "message": None
}


def save_crawled_data(data: List[dict], db: Session):
    saved_count = 0
    for item in data:
        try:
            existing = db.query(Transaction).filter(
                Transaction.community == item.get('community'),
                Transaction.transaction_date == item.get('transaction_date'),
                Transaction.area == item.get('area')
            ).first()
            
            if not existing:
                transaction = Transaction(**item)
                db.add(transaction)
                saved_count += 1
        except Exception as e:
            print(f"保存数据失败: {e}")
            continue
    
    db.commit()
    return saved_count


async def run_crawler_task(city: str, regions: List[str], pages: int):
    global crawler_status
    crawler_status["is_running"] = True
    
    try:
        data = await crawl_lianjia_data(city, regions, pages)
        
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            saved = save_crawled_data(data, db)
            crawler_status["total_crawled"] = saved
        finally:
            db.close()
            
    except Exception as e:
        print(f"爬虫任务失败: {e}")
    finally:
        from datetime import datetime
        crawler_status["is_running"] = False
        crawler_status["last_run"] = datetime.now().isoformat()
        crawler_status["current_region"] = None


@router.post("/start", response_model=ApiResponse)
async def start_crawler(
    background_tasks: BackgroundTasks,
    city: str = "bj",
    regions: Optional[str] = None,
    pages: int = 3,
    db: Session = Depends(get_db)
):
    global crawler_status
    
    if crawler_status["is_running"]:
        raise HTTPException(status_code=400, detail="爬虫正在运行中，请稍后再试")
    
    region_list = regions.split(",") if regions else None
    
    background_tasks.add_task(run_crawler_task, city, region_list, pages)
    
    return ApiResponse(
        message="爬虫任务已启动",
        data={"city": city, "regions": region_list, "pages": pages}
    )


@router.get("/status")
def get_crawler_status():
    return crawler_status


@router.get("/cities")
def get_supported_cities():
    return {
        "cities": [
            {"code": "bj", "name": "北京"},
            {"code": "sh", "name": "上海"},
            {"code": "gz", "name": "广州"},
            {"code": "sz", "name": "深圳"},
            {"code": "hz", "name": "杭州"},
            {"code": "nj", "name": "南京"},
            {"code": "cd", "name": "成都"},
            {"code": "wh", "name": "武汉"},
            {"code": "tj", "name": "天津"},
            {"code": "xa", "name": "西安"},
        ]
    }


async def run_government_crawler_task(city: str):
    global government_crawler_status
    government_crawler_status["is_running"] = True
    government_crawler_status["city"] = city
    
    try:
        if city == "sh" or city == "上海":
            result = crawl_shanghai_housing()
            government_crawler_status["message"] = f"成功获取上海房管局数据"
        else:
            government_crawler_status["message"] = f"暂不支持该城市: {city}"
            
    except Exception as e:
        government_crawler_status["message"] = f"爬取失败: {str(e)}"
    finally:
        from datetime import datetime
        government_crawler_status["is_running"] = False
        government_crawler_status["last_run"] = datetime.now().isoformat()


@router.post("/government/start", response_model=ApiResponse)
async def start_government_crawler(
    background_tasks: BackgroundTasks,
    city: str = "sh"
):
    global government_crawler_status
    
    if government_crawler_status["is_running"]:
        raise HTTPException(status_code=400, detail="政府数据爬虫正在运行中，请稍后再试")
    
    background_tasks.add_task(run_government_crawler_task, city)
    
    return ApiResponse(
        message="政府数据爬虫任务已启动",
        data={"city": city}
    )


@router.get("/government/status")
def get_government_crawler_status():
    return government_crawler_status


@router.get("/government/cities")
def get_supported_government_cities():
    return {
        "cities": [
            {"code": "sh", "name": "上海", "source": "上海市房地产交易中心"},
        ],
        "note": "更多城市正在开发中"
    }
