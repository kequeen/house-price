import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import re

from app.config import settings


class LianjiaCrawler:
    def __init__(self, city: str = "bj"):
        self.city = city
        self.base_url = f"https://{city}.lianjia.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> Optional[str]:
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            print(f"请求失败: {url}, 错误: {e}")
        return None

    def parse_transaction_item(self, item_html: str, region: str) -> Optional[Dict]:
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

    async def crawl_chengjiao(
        self, 
        region: str, 
        pages: int = 1
    ) -> List[Dict]:
        results = []
        url_template = f"{self.base_url}/chengjiao/{region}/pg{{page}}"
        
        for page in range(1, pages + 1):
            url = url_template.format(page=page)
            html = await self.fetch_page(url)
            
            if not html:
                continue
            
            soup = BeautifulSoup(html, 'lxml')
            items = soup.select('.list .clear')
            
            for item in items:
                data = self.parse_transaction_item(str(item), region)
                if data:
                    results.append(data)
            
            await asyncio.sleep(1)
        
        return results

    async def get_regions(self) -> List[str]:
        url = f"{self.base_url}/chengjiao/"
        html = await self.fetch_page(url)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        region_links = soup.select('.position a[data-role="ershoufang"]')
        
        regions = []
        for link in region_links:
            href = link.get('href', '')
            if '/chengjiao/' in href:
                region = href.split('/chengjiao/')[-1].rstrip('/')
                if region:
                    regions.append(region)
        
        return regions


async def crawl_lianjia_data(city: str = "bj", regions: List[str] = None, pages_per_region: int = 3):
    all_data = []
    
    async with LianjiaCrawler(city) as crawler:
        if not regions:
            regions = await crawler.get_regions()
            print(f"获取到 {len(regions)} 个区域")
        
        for region in regions:
            print(f"正在爬取区域: {region}")
            data = await crawler.crawl_chengjiao(region, pages=pages_per_region)
            all_data.extend(data)
            print(f"区域 {region} 获取到 {len(data)} 条数据")
    
    return all_data
