import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
import random

from app.database import SessionLocal, init_db
from app.models.transaction import Transaction

SHANGHAI_REGIONS = {
    '浦东新区': {
        'districts': ['陆家嘴', '张江', '金桥', '川沙', '周浦', '三林', '北蔡', '花木', '源深', '世纪公园'],
        'price_range': (60000, 150000)
    },
    '闵行区': {
        'districts': ['莘庄', '七宝', '虹桥', '梅陇', '古美', '龙柏', '华漕', '浦江'],
        'price_range': (45000, 90000)
    },
    '徐汇区': {
        'districts': ['徐家汇', '衡山路', '田林', '漕河泾', '龙华', '上海南站', '康健'],
        'price_range': (70000, 140000)
    },
    '静安区': {
        'districts': ['南京西路', '大宁', '彭浦', '不夜城', '曹家渡'],
        'price_range': (75000, 150000)
    },
    '黄浦区': {
        'districts': ['人民广场', '外滩', '新天地', '豫园', '打浦桥'],
        'price_range': (90000, 180000)
    },
    '长宁区': {
        'districts': ['中山公园', '虹桥', '古北', '天山', '新华路', '动物园'],
        'price_range': (60000, 120000)
    },
    '普陀区': {
        'districts': ['长风', '真如', '万里', '曹杨', '武宁', '桃浦'],
        'price_range': (50000, 90000)
    },
    '虹口区': {
        'districts': ['四川北路', '北外滩', '曲阳', '凉城', '江湾镇'],
        'price_range': (55000, 100000)
    },
    '杨浦区': {
        'districts': ['五角场', '新江湾城', '控江路', '中原', '黄兴公园'],
        'price_range': (50000, 95000)
    },
    '宝山区': {
        'districts': ['共康', '大华', '淞宝', '罗店', '顾村', '杨行'],
        'price_range': (35000, 65000)
    },
    '嘉定区': {
        'districts': ['嘉定新城', '南翔', '安亭', '江桥', '马陆'],
        'price_range': (30000, 60000)
    },
    '松江区': {
        'districts': ['松江新城', '九亭', '泗泾', '佘山', '大学城'],
        'price_range': (28000, 55000)
    },
    '青浦区': {
        'districts': ['青浦新城', '徐泾', '赵巷', '华新'],
        'price_range': (30000, 60000)
    },
    '奉贤区': {
        'districts': ['南桥', '奉城', '海湾'],
        'price_range': (22000, 45000)
    }
}

COMMUNITIES = {
    '陆家嘴': ['世茂滨江花园', '仁恒滨江园', '汤臣一品', '中粮海景一号', '盛大金磐'],
    '张江': ['张江汤臣豪园', '城市经典家园', '中芯花园', '张江公馆'],
    '莘庄': ['上海春城', '康城', '好世鹿鸣苑', '名都新城'],
    '徐家汇': ['东方曼哈顿', '汇贤雅居', '莱诗邸', '徐汇苑'],
    '中山公园': ['圣约翰名邸', '凯欣豪园', '路易凯旋宫', '虹桥新城'],
    '五角场': ['文化花园', '新江湾城首府', '合生江湾国际公寓'],
    '南京西路': ['静安豪庭', '中凯城市之光', '国际丽都城'],
    '人民广场': ['翠湖天地', '华府天地', '复兴珑御'],
    '花木': ['浦东星河湾', '仁恒河滨城', '联洋年华园'],
    '金桥': ['金桥名都', '碧云新天地', '爱法新城'],
}

ORIENTATIONS = ['南北', '东南', '西南', '东北', '西北', '东', '南', '西', '北']
DECORATIONS = ['精装', '简装', '毛坯', '中装']
PROPERTY_TYPES = ['住宅', '公寓', '别墅']


def generate_shanghai_data(count=1000):
    db = SessionLocal()
    
    try:
        init_db()
        
        base_date = datetime(2024, 1, 1)
        
        for i in range(count):
            region = random.choice(list(SHANGHAI_REGIONS.keys()))
            region_data = SHANGHAI_REGIONS[region]
            district = random.choice(region_data['districts'])
            
            communities = COMMUNITIES.get(district, [f'{district}花园{i+1}' for i in range(3)])
            community = random.choice(communities)
            
            days_offset = random.randint(0, 365)
            transaction_date = base_date + timedelta(days=days_offset)
            
            area = round(random.uniform(50, 200), 2)
            
            min_price, max_price = region_data['price_range']
            base_unit_price = random.uniform(min_price, max_price)
            
            if district in ['陆家嘴', '徐家汇', '南京西路', '人民广场', '新天地']:
                base_unit_price *= 1.2
            elif district in ['张江', '金桥', '莘庄']:
                base_unit_price *= 0.95
            
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
                data_source='lianjia'
            )
            
            db.add(transaction)
        
        db.commit()
        print(f'成功生成 {count} 条上海房价数据')
        
    except Exception as e:
        print(f'生成数据失败: {e}')
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    generate_shanghai_data(1000)
