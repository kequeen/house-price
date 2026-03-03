import sys
sys.path.insert(0, '.')

import asyncio
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
import re
from app.database import SessionLocal, init_db
from app.models.transaction import Transaction


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}


async def fetch_page(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"请求失败: {url}, 状态码: {response.status}")
    except Exception as e:
        print(f"请求异常: {url}, 错误: {e}")
    return None


def parse_transaction_item(item_html, region):
    try:
        soup = BeautifulSoup(item_html, 'lxml')
        
        community = soup.select_one('.houseInfo a')
        community_name = community.text.strip() if community else None
        
        house_info = soup.select_one('.houseInfo')
        house_text = house_info.text if house_info else ""
        
        area_match = re.search(r'(\d+\.?\d*)平米', house_text)
        area = float(area_match.group(1)) if area_match else None
        
        bedrooms_match = re.search(r'(\d+)室', house_text)
        bedrooms = int(bedrooms_match.group(1)) if bedrooms_match else None
        
        living_match = re.search(r'(\d+)厅', house_text)
        living_rooms = int(living_match.group(1)) if living_match else None
        
        orientation_match = re.search(r'(东|南|西|北|东南|东北|西南|西北|南北|东西)', house_text)
        orientation = orientation_match.group(1) if orientation_match else None
        
        floor_info = soup.select_one('.positionInfo')
        floor_text = floor_info.text if floor_info else ""
        
        deal_date = soup.select_one('.dealDate')
        date_str = deal_date.text.strip() if deal_date else None
        
        transaction_date = None
        year = None
        month = None
        if date_str:
            try:
                transaction_date = datetime.strptime(date_str, "%Y.%m.%d")
                year = transaction_date.year
                month = transaction_date.month
            except:
                pass
        
        total_price = soup.select_one('.totalPrice span')
        price = float(total_price.text) if total_price else None
        
        unit_price_elem = soup.select_one('.unitPrice span')
        unit_price_text = unit_price_elem.text if unit_price_elem else ""
        unit_price_match = re.search(r'(\d+)', unit_price_text.replace(',', ''))
        unit_price = float(unit_price_match.group(1)) if unit_price_match else None
        
        return {
            'region': region,
            'community': community_name,
            'area': area,
            'bedrooms': bedrooms,
            'living_rooms': living_rooms,
            'orientation': orientation,
            'floor': floor_text,
            'transaction_date': transaction_date,
            'year': year,
            'month': month,
            'price': price,
            'unit_price': unit_price,
            'property_type': '住宅',
            'data_source': 'lianjia'
        }
    except Exception as e:
        print(f"解析失败: {e}")
        return None


async def fetch_shanghai_data():
    print("开始获取上海链家成交数据...")
    
    db = SessionLocal()
    init_db()
    
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            regions_url = "https://sh.lianjia.com/chengjiao/"
            print(f"获取区域列表: {regions_url}")
            html = await fetch_page(session, regions_url)
            
            if not html:
                print("无法获取区域列表，使用预设区域")
                regions = ['pudong', 'minhang', 'baoshan', 'jiading', 'songjiang', 
                          'qingpu', 'fengxian', 'jinshan', 'xuhui', 'changning',
                          'jingan', 'putuo', 'hongkou', 'yangpu', 'huangpu']
            else:
                soup = BeautifulSoup(html, 'lxml')
                region_links = soup.select('.position a[data-role="ershoufang"]')
                regions = []
                for link in region_links:
                    href = link.get('href', '')
                    if '/chengjiao/' in href:
                        region = href.split('/chengjiao/')[-1].rstrip('/')
                        if region:
                            regions.append(region)
                
                if not regions:
                    print("解析区域失败，使用预设区域")
                    regions = ['pudong', 'minhang', 'baoshan', 'jiading', 'songjiang']
            
            print(f"区域列表: {regions}")
            
            total_count = 0
            
            for region in regions[:5]:
                print(f"\n正在爬取区域: {region}")
                
                for page in range(1, 3):
                    url = f"https://sh.lianjia.com/chengjiao/{region}/pg{page}"
                    print(f"  请求: {url}")
                    html = await fetch_page(session, url)
                    
                    if not html:
                        continue
                    
                    soup = BeautifulSoup(html, 'lxml')
                    items = soup.select('.list .clear')
                    
                    if not items:
                        items = soup.select('.chengjiao-item')
                    
                    if not items:
                        items = soup.select('ul.list li')
                    
                    print(f"  找到 {len(items)} 条记录")
                    
                    for item in items:
                        data = parse_transaction_item(str(item), region)
                        if data and data.get('community'):
                            try:
                                existing = db.query(Transaction).filter(
                                    Transaction.community == data.get('community'),
                                    Transaction.transaction_date == data.get('transaction_date'),
                                    Transaction.area == data.get('area')
                                ).first()
                                
                                if not existing:
                                    transaction = Transaction(**data)
                                    db.add(transaction)
                                    total_count += 1
                            except Exception as e:
                                continue
                    
                    await asyncio.sleep(2)
                
                db.commit()
                print(f"区域 {region} 完成")
                await asyncio.sleep(3)
            
            print(f"\n总共保存 {total_count} 条新数据")
            
        except Exception as e:
            print(f"爬取失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()


if __name__ == '__main__':
    asyncio.run(fetch_shanghai_data())
