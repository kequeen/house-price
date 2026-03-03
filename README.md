# 房价分析系统

一个完整的房价数据分析系统，支持从链家等平台采集数据，导入房管局数据，获取政府公开统计数据，并提供可视化分析界面。

## 功能特点

- **数据采集**：支持从链家网站采集成交数据
- **政府数据**：获取国家统计局70城房价变动数据
- **数据导入**：支持CSV、Excel格式的房管局数据导入
- **数据分析**：按年/月/区域统计成交量和成交价
- **可视化展示**：价格趋势图、成交量趋势图、区域对比图
- **RESTful API**：完整的后端API接口

## 技术栈

### 后端
- Python 3.10+
- FastAPI - Web框架
- SQLAlchemy - ORM
- SQLite - 数据库
- BeautifulSoup4 - 网页解析
- Pandas - 数据处理

### 前端
- Vue 3 - 前端框架
- Element Plus - UI组件库
- ECharts - 图表库
- Vite - 构建工具

## 项目结构

```
house-price/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API接口
│   │   ├── crawlers/       # 爬虫模块
│   │   ├── fetchers/       # 政府数据获取
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # 数据验证
│   │   ├── config.py       # 配置
│   │   ├── database.py     # 数据库
│   │   └── main.py         # 入口
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── api/           # API调用
│   │   ├── router/        # 路由
│   │   ├── views/         # 页面
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── start.sh               # 启动脚本
└── install.sh             # 安装脚本
```

## 快速开始

### 1. 安装依赖

```bash
chmod +x install.sh start.sh
./install.sh
```

或手动安装：

```bash
# 后端
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

### 2. 启动服务

```bash
./start.sh
```

或手动启动：

```bash
# 后端
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm run dev
```

### 3. 访问系统

- 前端界面：http://localhost:5173
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

## 数据来源

### 1. 政府公开数据（推荐）

系统支持获取国家统计局公布的70个大中城市房价变动数据：

- **数据来源**：国家统计局月度数据
- **覆盖城市**：70个大中城市
- **数据内容**：新房/二手房成交量、平均价格、价格变动指数
- **更新频率**：月度

```bash
# 获取政府数据
cd backend
source .venv/bin/activate
python -c "from app.fetchers.government_data import fetch_government_data; fetch_government_data()"
```

### 2. 链家数据采集

支持从链家网站采集成交数据（需注意反爬限制）

### 3. 手动导入

支持CSV和Excel格式的数据导入，适用于房管局公布的网签数据

## API接口

### 成交数据

| 方法 | 接口 | 说明 |
|------|------|------|
| GET | /api/transactions | 获取成交列表 |
| GET | /api/transactions/stats/monthly | 月度统计 |
| GET | /api/transactions/stats/regions | 区域统计 |
| GET | /api/transactions/trends/price | 价格趋势 |
| GET | /api/transactions/trends/volume | 成交量趋势 |

### 政府数据

| 方法 | 接口 | 说明 |
|------|------|------|
| GET | /api/government/summary | 数据概览 |
| GET | /api/government/stats/cities | 城市统计 |
| GET | /api/government/rankings | 城市排行 |
| GET | /api/government/trend/{city} | 城市趋势 |
| GET | /api/government/compare | 城市对比 |

### 数据导入

| 方法 | 接口 | 说明 |
|------|------|------|
| POST | /api/data/import/csv | 导入CSV |
| POST | /api/data/import/excel | 导入Excel |
| GET | /api/data/template | 获取导入模板 |

### 数据采集

| 方法 | 接口 | 说明 |
|------|------|------|
| POST | /api/crawler/start | 启动爬虫 |
| GET | /api/crawler/status | 爬虫状态 |
| GET | /api/crawler/cities | 支持的城市 |

## 数据格式

导入数据支持以下字段：

| 字段 | 说明 | 必填 |
|------|------|------|
| region | 区域 | 是 |
| district | 片区 | 否 |
| community | 小区名称 | 否 |
| transaction_date | 成交日期 | 否 |
| price | 成交总价(万元) | 否 |
| unit_price | 单价(元/平米) | 否 |
| area | 面积(平米) | 否 |
| property_type | 物业类型 | 否 |
| floor | 楼层 | 否 |
| orientation | 朝向 | 否 |
| decoration | 装修情况 | 否 |
| bedrooms | 卧室数量 | 否 |
| living_rooms | 客厅数量 | 否 |

## 注意事项

1. 爬虫仅供学习研究使用，请遵守网站使用条款
2. 建议在非高峰时段运行爬虫
3. 数据采集已做限速处理
4. 政府数据为模拟数据，真实数据需从国家统计局官网获取

## License

MIT
