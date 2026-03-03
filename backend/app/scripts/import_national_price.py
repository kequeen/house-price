import sys
sys.path.insert(0, '.')

from app.database import SessionLocal, init_db
from app.models.region import NationalPriceStats

NATIONAL_PRICE_DATA = [
    {"year": 2016, "new_commercial_avg_price": 7699, "residential_avg_price": 7433, "office_avg_price": 14725, "commercial_building_avg_price": 9917, "other_avg_price": 4905},
    {"year": 2017, "new_commercial_avg_price": 8160, "residential_avg_price": 7893, "office_avg_price": 14019, "commercial_building_avg_price": 10512, "other_avg_price": 5459},
    {"year": 2018, "new_commercial_avg_price": 9045, "residential_avg_price": 8886, "office_avg_price": 14890, "commercial_building_avg_price": 11107, "other_avg_price": 5445},
    {"year": 2019, "new_commercial_avg_price": 9673, "residential_avg_price": 9667, "office_avg_price": 14840, "commercial_building_avg_price": 11170, "other_avg_price": 5180},
    {"year": 2020, "new_commercial_avg_price": 10248, "residential_avg_price": 10385, "office_avg_price": 15697, "commercial_building_avg_price": 10887, "other_avg_price": 4877},
    {"year": 2021, "new_commercial_avg_price": 10546, "residential_avg_price": 10825, "office_avg_price": 14444, "commercial_building_avg_price": 10969, "other_avg_price": 4675},
    {"year": 2022, "new_commercial_avg_price": 10210, "residential_avg_price": 10608, "office_avg_price": 14385, "commercial_building_avg_price": 10097, "other_avg_price": 4104},
    {"year": 2023, "new_commercial_avg_price": 10438, "residential_avg_price": 10864, "office_avg_price": 13781, "commercial_building_avg_price": 10422, "other_avg_price": 4165},
    {"year": 2024, "new_commercial_avg_price": 9935, "residential_avg_price": 10419, "office_avg_price": 13350, "commercial_building_avg_price": 9569, "other_avg_price": None},
]


def import_national_price_data():
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("导入国家统计局全国房价数据")
        print("=" * 60)
        
        saved_count = 0
        updated_count = 0
        
        for data in NATIONAL_PRICE_DATA:
            existing = db.query(NationalPriceStats).filter(
                NationalPriceStats.year == data["year"]
            ).first()
            
            if existing:
                existing.new_commercial_avg_price = data["new_commercial_avg_price"]
                existing.residential_avg_price = data["residential_avg_price"]
                existing.office_avg_price = data["office_avg_price"]
                existing.commercial_building_avg_price = data["commercial_building_avg_price"]
                existing.other_avg_price = data.get("other_avg_price")
                existing.data_source = "国家统计局"
                updated_count += 1
                print(f"  更新 {data['year']} 年数据")
            else:
                stats = NationalPriceStats(
                    year=data["year"],
                    new_commercial_avg_price=data["new_commercial_avg_price"],
                    residential_avg_price=data["residential_avg_price"],
                    office_avg_price=data["office_avg_price"],
                    commercial_building_avg_price=data["commercial_building_avg_price"],
                    other_avg_price=data.get("other_avg_price"),
                    data_source="国家统计局"
                )
                db.add(stats)
                saved_count += 1
                print(f"  新增 {data['year']} 年数据")
        
        db.commit()
        
        print(f"\n完成! 新增 {saved_count} 条, 更新 {updated_count} 条数据")
        return saved_count + updated_count
        
    except Exception as e:
        print(f"导入数据失败: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


if __name__ == '__main__':
    init_db()
    import_national_price_data()
