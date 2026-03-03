<template>
  <div class="government-data">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">覆盖城市</div>
          <div class="stat-value">{{ summary.city_count || 332 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">总成交量</div>
          <div class="stat-value">{{ formatNumber(summary.total_transactions) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">平均单价</div>
          <div class="stat-value">{{ formatPrice(summary.avg_price) }} 元/㎡</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">数据时间跨度</div>
          <div class="stat-value">2005-2024</div>
          <div class="stat-sub">20年历史数据</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>全国商品房平均销售价格趋势 (国家统计局官方数据)</span>
              <el-tag type="success" size="small">数据来源: 国家统计局</el-tag>
            </div>
          </template>
          <el-row :gutter="20">
            <el-col :span="18">
              <div ref="nationalChartRef" class="chart-container-large"></div>
            </el-col>
            <el-col :span="6">
              <div class="national-summary">
                <div class="summary-item">
                  <div class="summary-label">最新年份</div>
                  <div class="summary-value">{{ nationalSummary.latest_year || '-' }}年</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">商品房均价</div>
                  <div class="summary-value price">{{ formatPrice(nationalSummary.latest_price) }} 元/㎡</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">住宅均价</div>
                  <div class="summary-value">{{ formatPrice(nationalSummary.latest_residential_price) }} 元/㎡</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">历史最高</div>
                  <div class="summary-value peak">{{ nationalSummary.peak_year }}年 {{ formatPrice(nationalSummary.peak_price) }} 元/㎡</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">数据范围</div>
                  <div class="summary-value">{{ nationalSummary.year_range }}</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>城市房价排行 ({{ selectedYear }}年{{ selectedMonth }}月)</span>
              <div>
                <el-select v-model="selectedYear" size="small" style="width: 90px; margin-right: 10px;">
                  <el-option v-for="y in years" :key="y" :label="y + '年'" :value="y" />
                </el-select>
                <el-select v-model="selectedMonth" size="small" style="width: 80px;">
                  <el-option v-for="m in 12" :key="m" :label="m + '月'" :value="m" />
                </el-select>
              </div>
            </div>
          </template>
          <div ref="rankChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ selectedCity }}房价趋势 (20年)</span>
              <el-select v-model="selectedCity" placeholder="选择城市" size="small" style="width: 120px;" filterable>
                <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
              </el-select>
            </div>
          </template>
          <div ref="compareChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>全国房价年度数据 (国家统计局)</span>
              <el-button type="primary" size="small" @click="exportNationalData">导出数据</el-button>
            </div>
          </template>
          <el-table :data="nationalPrices" style="width: 100%" max-height="300">
            <el-table-column prop="year" label="年份" width="80" />
            <el-table-column prop="new_commercial_avg_price" label="新建商品房均价(元/㎡)" width="180">
              <template #default="{ row }">
                {{ row.new_commercial_avg_price ? row.new_commercial_avg_price.toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="residential_avg_price" label="住宅均价(元/㎡)" width="150">
              <template #default="{ row }">
                {{ row.residential_avg_price ? row.residential_avg_price.toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="office_avg_price" label="办公楼均价(元/㎡)" width="150">
              <template #default="{ row }">
                {{ row.office_avg_price ? row.office_avg_price.toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="commercial_building_avg_price" label="商业营业用房均价(元/㎡)" width="180">
              <template #default="{ row }">
                {{ row.commercial_building_avg_price ? row.commercial_building_avg_price.toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="yoy_change" label="同比变化" width="100">
              <template #default="{ row }">
                <span :class="row.yoy_change >= 0 ? 'price-up' : 'price-down'">
                  {{ row.yoy_change ? (row.yoy_change >= 0 ? '+' : '') + row.yoy_change + '%' : '-' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="data_source" label="数据来源" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>城市详细数据 ({{ selectedYear }}年{{ selectedMonth }}月)</span>
              <div>
                <el-input v-model="citySearch" placeholder="搜索城市" size="small" style="width: 150px; margin-right: 10px;" clearable />
                <el-button type="primary" size="small" @click="exportData">导出数据</el-button>
              </div>
            </div>
          </template>
          <el-table :data="filteredCityStats" style="width: 100%" max-height="400">
            <el-table-column prop="city" label="城市" width="100" fixed />
            <el-table-column prop="year" label="年份" width="80" />
            <el-table-column prop="month" label="月份" width="80" />
            <el-table-column prop="avg_price" label="平均单价(元/㎡)" width="140">
              <template #default="{ row }">
                {{ row.avg_price ? row.avg_price.toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="total_transactions" label="成交量(套)" width="120">
              <template #default="{ row }">
                {{ row.total_transactions ? row.total_transactions.toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="new_house_count" label="新房(套)" width="100">
              <template #default="{ row }">
                {{ row.new_house_count ? row.new_house_count.toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="second_hand_count" label="二手房(套)" width="100">
              <template #default="{ row }">
                {{ row.second_hand_count ? row.second_hand_count.toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="total_area" label="成交面积(㎡)" width="130">
              <template #default="{ row }">
                {{ row.total_area ? row.total_area.toLocaleString() : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="total_amount" label="成交金额(万元)" width="130">
              <template #default="{ row }">
                {{ row.total_amount ? (row.total_amount / 10000).toFixed(2) + ' 亿' : '-' }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import api from '../api'

const rankChartRef = ref(null)
const compareChartRef = ref(null)
const nationalChartRef = ref(null)

const summary = ref({})
const cityStats = ref([])
const cities = ref([])
const years = ref([])
const selectedYear = ref(2024)
const selectedMonth = ref(12)
const selectedCity = ref('北京')
const citySearch = ref('')
const nationalPrices = ref([])
const nationalSummary = ref({})

for (let y = 2024; y >= 2005; y--) {
  years.value.push(y)
}

let rankChart = null
let compareChart = null
let nationalChart = null

const filteredCityStats = computed(() => {
  if (!citySearch.value) return cityStats.value
  return cityStats.value.filter(item => item.city.includes(citySearch.value))
})

const formatNumber = (num) => {
  if (!num) return '-'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + ' 万'
  }
  return num.toLocaleString()
}

const formatPrice = (price) => {
  if (!price) return '-'
  return Math.round(price).toLocaleString()
}

const initCharts = () => {
  rankChart = echarts.init(rankChartRef.value)
  compareChart = echarts.init(compareChartRef.value)
  nationalChart = echarts.init(nationalChartRef.value)
}

const loadSummary = async () => {
  try {
    const { data } = await api.get('/government/summary')
    summary.value = data || {}
    if (data?.year) {
      selectedYear.value = data.year
      selectedMonth.value = data.month
    }
  } catch (e) {
    console.error('加载摘要失败', e)
  }
}

const loadCities = async () => {
  try {
    const { data } = await api.get('/government/cities/list')
    cities.value = data?.cities || []
  } catch (e) {
    console.error('加载城市列表失败', e)
  }
}

const loadNationalPrices = async () => {
  try {
    const [pricesRes, summaryRes] = await Promise.all([
      api.get('/government/national/prices'),
      api.get('/government/national/summary')
    ])
    
    nationalPrices.value = pricesRes.data?.data || []
    nationalSummary.value = summaryRes.data || {}
    
    renderNationalChart()
  } catch (e) {
    console.error('加载全国房价数据失败', e)
  }
}

const renderNationalChart = () => {
  if (!nationalChart || !nationalPrices.value.length) return
  
  const data = nationalPrices.value
  
  nationalChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['新建商品房', '住宅', '办公楼', '商业营业用房'],
      top: 0
    },
    grid: {
      left: 60,
      right: 60,
      top: 40,
      bottom: 40
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.year + '年'),
      axisLabel: { fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: '元/㎡',
      axisLabel: { formatter: v => (v / 1000) + 'k' }
    },
    series: [
      {
        name: '新建商品房',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data: data.map(d => d.new_commercial_avg_price),
        itemStyle: { color: '#409EFF' },
        lineStyle: { width: 3 }
      },
      {
        name: '住宅',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: data.map(d => d.residential_avg_price),
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '办公楼',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: data.map(d => d.office_avg_price),
        itemStyle: { color: '#E6A23C' }
      },
      {
        name: '商业营业用房',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: data.map(d => d.commercial_building_avg_price),
        itemStyle: { color: '#F56C6C' }
      }
    ]
  })
}

const loadRankings = async () => {
  try {
    const { data } = await api.get(`/government/rankings?year=${selectedYear.value}&month=${selectedMonth.value}&limit=20`)
    
    const rankings = data?.rankings || []
    rankChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 80, right: 30, top: 20, bottom: 30 },
      xAxis: {
        type: 'value',
        name: '元/㎡',
        axisLabel: { formatter: v => (v / 1000) + 'k' }
      },
      yAxis: {
        type: 'category',
        data: rankings.map(r => r.city).reverse(),
        axisLabel: { fontSize: 11 }
      },
      series: [{
        name: '平均单价',
        type: 'bar',
        data: rankings.map(r => r.avg_price).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#409EFF' },
            { offset: 1, color: '#67C23A' }
          ])
        }
      }]
    })
  } catch (e) {
    console.error('加载排行失败', e)
  }
}

const loadCityTrend = async () => {
  if (!selectedCity.value) return
  
  try {
    const { data } = await api.get(`/government/trend/${selectedCity.value}`)
    
    const trendData = data?.data || []
    compareChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['平均单价', '成交量'], top: 0 },
      grid: { left: 60, right: 60, top: 40, bottom: 50 },
      xAxis: {
        type: 'category',
        data: trendData.map(d => d.date),
        axisLabel: { rotate: 45, fontSize: 9, interval: 23 }
      },
      yAxis: [
        {
          type: 'value',
          name: '元/㎡',
          position: 'left',
          axisLabel: { formatter: v => (v / 1000) + 'k' }
        },
        {
          type: 'value',
          name: '成交量',
          position: 'right'
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100
        },
        {
          type: 'slider',
          start: 0,
          end: 100,
          height: 20,
          bottom: 5
        }
      ],
      series: [
        {
          name: '平均单价',
          type: 'line',
          smooth: true,
          symbol: 'none',
          data: trendData.map(d => d.avg_price),
          itemStyle: { color: '#409EFF' },
          areaStyle: { opacity: 0.1 }
        },
        {
          name: '成交量',
          type: 'bar',
          yAxisIndex: 1,
          data: trendData.map(d => d.total_transactions),
          itemStyle: { color: '#67C23A', opacity: 0.5 }
        }
      ]
    })
  } catch (e) {
    console.error('加载趋势失败', e)
  }
}

const loadCityStats = async () => {
  try {
    const { data } = await api.get(`/government/stats/cities?year=${selectedYear.value}&month=${selectedMonth.value}`)
    cityStats.value = data?.items || []
  } catch (e) {
    console.error('加载城市统计失败', e)
  }
}

const exportData = () => {
  const headers = ['城市', '年份', '月份', '平均单价', '成交量', '新房', '二手房', '成交面积', '成交金额']
  const rows = cityStats.value.map(r => [
    r.city, r.year, r.month, r.avg_price, r.total_transactions,
    r.new_house_count, r.second_hand_count, r.total_area, r.total_amount
  ])
  
  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `全国房价数据_${selectedYear.value}年${selectedMonth.value}月.csv`
  link.click()
  URL.revokeObjectURL(url)
}

const exportNationalData = () => {
  const headers = ['年份', '新建商品房均价', '住宅均价', '办公楼均价', '商业营业用房均价', '同比变化', '数据来源']
  const rows = nationalPrices.value.map(r => [
    r.year, 
    r.new_commercial_avg_price, 
    r.residential_avg_price, 
    r.office_avg_price, 
    r.commercial_building_avg_price,
    r.yoy_change ? r.yoy_change + '%' : '',
    r.data_source
  ])
  
  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `全国商品房平均销售价格_国家统计局.csv`
  link.click()
  URL.revokeObjectURL(url)
}

watch([selectedYear, selectedMonth], () => {
  loadRankings()
  loadCityStats()
})

watch(selectedCity, () => {
  loadCityTrend()
})

onMounted(async () => {
  initCharts()
  await Promise.all([loadSummary(), loadCities(), loadNationalPrices()])
  await Promise.all([loadRankings(), loadCityTrend(), loadCityStats()])
  
  window.addEventListener('resize', () => {
    rankChart?.resize()
    compareChart?.resize()
    nationalChart?.resize()
  })
})
</script>

<style scoped>
.government-data {
  width: 100%;
}

.stat-card {
  text-align: center;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
}

.chart-container-large {
  height: 350px;
}

.national-summary {
  padding: 10px;
}

.summary-item {
  padding: 12px 0;
  border-bottom: 1px solid #EBEEF5;
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.summary-value.price {
  color: #409EFF;
}

.summary-value.peak {
  color: #E6A23C;
}

.price-up {
  color: #F56C6C;
  font-weight: bold;
}

.price-down {
  color: #67C23A;
  font-weight: bold;
}
</style>
