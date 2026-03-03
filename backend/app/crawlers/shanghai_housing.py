import sys
sys.path.insert(0, '.')

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
from app.database import SessionLocal, init_db
from app.models.region import CityMonthlyStats


class ShanghaiHousingCrawler:
    BASE_URL = "https://www.fangdi.com.cn"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.fangdi.com.cn/'
        })
    
    def get_market_overview(self):
        """获取上海房地产市场概览数据"""
        try:
            response = self.session.get(self.BASE_URL, timeout=30)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'new_house': {'units': 0, 'area': 0},
                'second_hand': {'units': 0, 'area': 0},
                'today_sign': {'units': 0, 'area': 0}
            }
            
            text = response.text
            
            units_match = re.search(r'一手房签约套数[：:\s]*(\d+)\s*套', text)
            if units_match:
                data['today_sign']['units'] = int(units_match.group(1))
            
            area_match = re.search(r'一手房签约面积[：:\s]*([\d.]+)\s*㎡', text)
            if area_match:
                data['today_sign']['area'] = float(area_match.group(1))
            
            new_house_match = re.search(r'可售住宅[^>]*>[\s\S]*?(\d+)[^<]*<[\s\S]*?(\d+\.?\d*)', text)
            if new_house_match:
                data['new_house']['units'] = int(new_house_match.group(1))
                data['new_house']['area'] = float(new_house_match.group(2))
            
            second_hand_match = re.search(r'二手房住宅挂牌[^>]*>[\s\S]*?(\d+)[^<]*<[\s\S]*?(\d+\.?\d*)', text)
            if second_hand_match:
                data['second_hand']['units'] = int(second_hand_match.group(1))
                data['second_hand']['area'] = float(second_hand_match.group(2))
            
            print(f"   解析到数据: 今日签约 {data['today_sign']['units']}套")
            
            return data
            
        except Exception as e:
            print(f"获取市场概览失败: {e}")
            return None
    
    def get_district_stats(self):
        """获取各区成交统计数据"""
        try:
            response = self.session.get(self.BASE_URL, timeout=30)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            district_data = []
            
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        district_name = cols[0].get_text(strip=True)
                        if district_name in ['浦东新区', '黄浦区', '徐汇区', '长宁区', '静安区', 
                                             '普陀区', '虹口区', '杨浦区', '闵行区', '宝山区',
                                             '嘉定区', '金山区', '松江区', '青浦区', '奉贤区', '崇明区']:
                            data = {
                                'district': district_name,
                                'new_house_units': cols[1].get_text(strip=True) if len(cols) > 1 else '0',
                                'new_house_area': cols[2].get_text(strip=True) if len(cols) > 2 else '0',
                                'second_hand_units': cols[3].get_text(strip=True) if len(cols) > 3 else '0',
                                'second_hand_area': cols[4].get_text(strip=True) if len(cols) > 4 else '0'
                            }
                            district_data.append(data)
            
            return district_data
            
        except Exception as e:
            print(f"获取各区数据失败: {e}")
            return []
    
    def get_daily_transaction(self):
        """获取今日成交数据"""
        try:
            url = f"{self.BASE_URL}/statistic/data.html"
            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'new_house': {
                    'units': 0,
                    'area': 0
                },
                'second_hand': {
                    'units': 0,
                    'area': 0
                }
            }
            
            units_match = re.search(r'一手房签约套数[：:]\s*(\d+)套', response.text)
            if units_match:
                data['new_house']['units'] = int(units_match.group(1))
            
            area_match = re.search(r'一手房签约面积[：:]\s*([\d.]+)㎡', response.text)
            if area_match:
                data['new_house']['area'] = float(area_match.group(1))
            
            return data
            
        except Exception as e:
            print(f"获取今日成交数据失败: {e}")
            return None
    
    def save_to_database(self, data):
        """保存数据到数据库"""
        db = SessionLocal()
        
        try:
            today = datetime.now()
            
            existing = db.query(CityMonthlyStats).filter(
                CityMonthlyStats.city == '上海',
                CityMonthlyStats.year == today.year,
                CityMonthlyStats.month == today.month
            ).first()
            
            if existing:
                existing.total_transactions = data.get('new_house', {}).get('units', 0)
                existing.total_area = data.get('new_house', {}).get('area', 0)
                existing.data_source = '上海房管局'
                existing.updated_at = datetime.now()
            else:
                stats = CityMonthlyStats(
                    city='上海',
                    year=today.year,
                    month=today.month,
                    total_transactions=data.get('new_house', {}).get('units', 0),
                    total_area=data.get('new_house', {}).get('area', 0),
                    total_amount=0,
                    avg_price=0,
                    new_house_count=data.get('new_house', {}).get('units', 0),
                    second_hand_count=data.get('second_hand', {}).get('units', 0),
                    data_source='上海房管局'
                )
                db.add(stats)
            
            db.commit()
            print(f"数据已保存: {today.year}年{today.month}月")
            
        except Exception as e:
            print(f"保存数据失败: {e}")
            db.rollback()
        finally:
            db.close()


def crawl_shanghai_housing():
    """爬取上海房管局数据"""
    crawler = ShanghaiHousingCrawler()
    
    print("=" * 60)
    print("上海房管局数据爬取")
    print("=" * 60)
    
    print("\n1. 获取市场概览...")
    overview = crawler.get_market_overview()
    if overview:
        print(f"   日期: {overview['date']}")
        print(f"   今日签约: {overview.get('today_sign', {})}")
    
    print("\n2. 获取今日成交数据...")
    daily = crawler.get_daily_transaction()
    if daily:
        print(f"   新房成交: {daily['new_house']['units']}套, {daily['new_house']['area']}㎡")
    
    print("\n3. 保存数据到数据库...")
    if daily:
        crawler.save_to_database(daily)
    
    print("\n完成!")
    
    return {
        'overview': overview,
        'daily': daily
    }


if __name__ == '__main__':
    init_db()
    result = crawl_shanghai_housing()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
