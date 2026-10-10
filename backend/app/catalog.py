"""国家统计局70城分类的一、二线城市；不采用商业机构的‘新一线’分类。"""
TIER_SOURCE_URL = 'https://www.stats.gov.cn/sj/sjjd/202609/t20260915_1965303.html'
FIRST_TIER = ['北京', '上海', '广州', '深圳']
SECOND_TIER = ['天津', '石家庄', '太原', '呼和浩特', '沈阳', '大连', '长春', '哈尔滨',
               '南京', '杭州', '宁波', '合肥', '福州', '厦门', '南昌', '济南', '青岛',
               '郑州', '武汉', '长沙', '南宁', '海口', '重庆', '成都', '贵阳', '昆明',
               '西安', '兰州', '西宁', '银川', '乌鲁木齐']
PROVINCES = ['天津', '河北', '山西', '内蒙古', '辽宁', '辽宁', '吉林', '黑龙江', '江苏',
             '浙江', '浙江', '安徽', '福建', '福建', '江西', '山东', '山东', '河南', '湖北',
             '湖南', '广西', '海南', '重庆', '四川', '贵州', '云南', '陕西', '甘肃', '青海',
             '宁夏', '新疆']
CITY_CATALOG = {c: {'tier': 1, 'province': p} for c, p in zip(FIRST_TIER, ['北京', '上海', '广东', '广东'])}
CITY_CATALOG.update({c: {'tier': 2, 'province': p} for c, p in zip(SECOND_TIER, PROVINCES)})

LOCAL_SOURCES = [
    {'key': 'beijing', 'city': '北京', 'name': '北京市住房和城乡建设委员会',
     'url': 'https://zjw.beijing.gov.cn/bjjs/fdcjy/wqht/fcsjtj/index.shtml',
     'adapter': True, 'note': '读取明确标注期间的住宅月度网签和年度住宅统计；网页可能滞后。'},
    {'key': 'shijiazhuang', 'city': '石家庄', 'name': '石家庄市住房和城乡建设局',
     'url': 'https://zjj.sjz.gov.cn/plus/list.php?tid=192',
     'adapter': True, 'note': '月度新建住宅与存量住房网签；统计范围为表内8个区，不代表整个行政市。'},
    {'key': 'shanghai', 'city': '上海', 'name': '上海市房地产交易中心',
     'url': 'https://www.fangdi.com.cn/', 'adapter': False,
     'note': '本次读取返回动态验证页，尚未接入；不以缺失值替代成交量。'},
    {'key': 'shenzhen', 'city': '深圳', 'name': '深圳市住房和建设局',
     'url': 'https://fdc.zjj.sz.gov.cn/public/marketInfo/tmcMonthDealInfo.html',
     'adapter': False, 'note': '本次读取返回动态验证页，尚未接入。'},
    {'key': 'guangzhou', 'city': '广州', 'name': '广州市住房和城乡建设局',
     'url': 'https://zfcj.gz.gov.cn/', 'adapter': False,
     'note': '官方数据查询入口已找到，尚未验证可持续读取的月度表。'},
]
