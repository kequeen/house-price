import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
import random

from app.database import SessionLocal, init_db
from app.models.transaction import Transaction

REGIONS = {
    '朝阳区': ['望京', '三里屯', '国贸', '大望路', '双井'],
    '海淀区': ['中关村', '五道口', '西二旗', '上地', '万柳'],
    '西城区': ['金融街', '西单', '德胜门', '广安门', '月坛'],
    '东城区': ['东直门', '建国门', '崇文门', '王府井', '安定门'],
    '丰台区': ['丽泽', '方庄', '大红门', '科技园区', '卢沟桥']
}

COMMUNITIES = {
    '望京': ['望京花园', '融科橄榄城', '望京新城', '利泽西园'],
    '三里屯': ['三里屯SOHO', '首开幸福广场', '工体北路小区'],
    '国贸': ['建外SOHO', '银泰中心', '国贸公寓', '华贸公寓'],
    '中关村': ['中关村南小区', '科育小区', '黄庄小区', '芙蓉里'],
    '五道口': ['华清嘉园', '东升园', '展春园小区'],
    '西二旗': ['领秀新硅谷', '融泽嘉园', '金域华府'],
    '金融街': ['金融街公寓', '丰汇园', '宏庙胡同'],
    '东直门': ['东直门北小街', '民安小区', '海运仓小区'],
    '丽泽': ['丽泽景园', '万年花城', '三环新城'],
    '方庄': ['芳古园', '芳城园', '芳群园', '芳星园']
}

ORIENTATIONS = ['南北', '东南', '西南', '东北', '西北', '东', '南', '西', '北']
DECORATIONS = ['精装', '简装', '毛坯', '中装']
PROPERTY_TYPES = ['住宅', '公寓', '别墅', '商住两用']


def generate_sample_data(count=500):
    db = SessionLocal()
    
    try:
        init_db()
        
        base_date = datetime(2024, 1, 1)
        
        for i in range(count):
            region = random.choice(list(REGIONS.keys()))
            district = random.choice(REGIONS[region])
            
            communities = COMMUNITIES.get(district, [f'{district}小区{i+1}' for i in range(3)])
            community = random.choice(communities)
            
            days_offset = random.randint(0, 365)
            transaction_date = base_date + timedelta(days=days_offset)
            
            area = round(random.uniform(50, 200), 2)
            base_unit_price = random.uniform(50000, 120000)
            
            if region in ['西城区', '东城区']:
                base_unit_price *= 1.3
            elif region in ['海淀区', '朝阳区']:
                base_unit_price *= 1.1
            
            unit_price = round(base_unit_price * random.uniform(0.9, 1.1), 0)
            price = round(area * unit_price / 10000, 2)
            
            bedrooms = random.randint(1, 5)
            living_rooms = random.randint(1, 3)
            
            transaction = Transaction(
                region=region,
                district=district,
                community=community,
                transaction_date=transaction_date,
                year=transaction_date.year,
                month=transaction_date.month,
                price=price,
                unit_price=unit_price,
                area=area,
                property_type=random.choice(PROPERTY_TYPES),
                floor=f'{random.choice(["高", "中", "低"])}/{random.randint(6, 30)}层',
                orientation=random.choice(ORIENTATIONS),
                decoration=random.choice(DECORATIONS),
                bedrooms=bedrooms,
                living_rooms=living_rooms,
                data_source=random.choice(['lianjia', 'government'])
            )
            
            db.add(transaction)
        
        db.commit()
        print(f'成功生成 {count} 条示例数据')
        
    except Exception as e:
        print(f'生成数据失败: {e}')
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    generate_sample_data(500)
