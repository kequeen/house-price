<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">总成交数</div>
          <div class="stat-value">{{ stats.totalTransactions }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">平均单价</div>
          <div class="stat-value">{{ formatPrice(stats.avgPrice) }} 元/㎡</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">成交总额</div>
          <div class="stat-value">{{ formatAmount(stats.totalAmount) }} 万元</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-title">覆盖区域</div>
          <div class="stat-value">{{ stats.regionCount }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>价格趋势</span>
              <el-select v-model="selectedRegion" placeholder="选择区域" clearable size="small" style="width: 150px;">
                <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
              </el-select>
            </div>
          </template>
          <div ref="priceChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>区域对比</span>
          </template>
          <div ref="regionChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>成交量趋势</span>
          </template>
          <div ref="volumeChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>月度统计</span>
          </template>
          <el-table :data="monthlyStats" style="width: 100%" max-height="300">
            <el-table-column prop="year" label="年份" width="80" />
            <el-table-column prop="month" label="月份" width="80" />
            <el-table-column prop="total_transactions" label="成交量" />
            <el-table-column prop="avg_price" label="平均单价">
              <template #default="{ row }">
                {{ row.avg_price ? row.avg_price.toFixed(0) : '-' }} 元/㎡
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { transactionApi } from '../api'

const priceChartRef = ref(null)
const regionChartRef = ref(null)
const volumeChartRef = ref(null)

const stats = ref({
  totalTransactions: 0,
  avgPrice: 0,
  totalAmount: 0,
  regionCount: 0
})

const regions = ref([])
const selectedRegion = ref('')
const monthlyStats = ref([])

let priceChart = null
let regionChart = null
let volumeChart = null

const formatPrice = (price) => {
  if (!price) return '-'
  return Math.round(price).toLocaleString()
}

const formatAmount = (amount) => {
  if (!amount) return '-'
  if (amount >= 10000) {
    return (amount / 10000).toFixed(2) + ' 亿'
  }
  return amount.toFixed(0)
}

const initCharts = () => {
  priceChart = echarts.init(priceChartRef.value)
  regionChart = echarts.init(regionChartRef.value)
  volumeChart = echarts.init(volumeChartRef.value)
}

const loadPriceTrend = async () => {
  try {
    const params = {}
    if (selectedRegion.value) {
      params.region = selectedRegion.value
    }
    const { data } = await transactionApi.getPriceTrend(params)
    
    const chartData = data || []
    priceChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: chartData.map(d => d.date)
      },
      yAxis: {
        type: 'value',
        name: '元/㎡'
      },
      series: [{
        name: '平均单价',
        type: 'line',
        smooth: true,
        data: chartData.map(d => d.avg_price),
        areaStyle: { opacity: 0.3 }
      }]
    })
  } catch (e) {
    console.error('加载价格趋势失败', e)
  }
}

const loadRegionStats = async () => {
  try {
    const { data } = await transactionApi.getRegionStats()
    
    const chartData = (data || []).slice(0, 10)
    regionChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: {
        type: 'category',
        data: chartData.map(d => d.region),
        axisLabel: { rotate: 45 }
      },
      yAxis: {
        type: 'value',
        name: '元/㎡'
      },
      series: [{
        name: '平均单价',
        type: 'bar',
        data: chartData.map(d => d.avg_price)
      }]
    })
    
    stats.value.regionCount = (data || []).length
  } catch (e) {
    console.error('加载区域统计失败', e)
  }
}

const loadVolumeTrend = async () => {
  try {
    const { data } = await transactionApi.getVolumeTrend()
    
    const chartData = data || []
    volumeChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: chartData.map(d => d.date)
      },
      yAxis: {
        type: 'value',
        name: '成交量'
      },
      series: [{
        name: '成交量',
        type: 'bar',
        data: chartData.map(d => d.volume)
      }]
    })
  } catch (e) {
    console.error('加载成交量趋势失败', e)
  }
}

const loadMonthlyStats = async () => {
  try {
    const { data } = await transactionApi.getMonthlyStats()
    monthlyStats.value = (data || []).slice(-12)
    
    if (data && data.length > 0) {
      stats.value.totalTransactions = data.reduce((sum, d) => sum + d.total_transactions, 0)
      stats.value.totalAmount = data.reduce((sum, d) => sum + (d.total_amount || 0), 0)
      
      const validPrices = data.filter(d => d.avg_price)
      if (validPrices.length > 0) {
        stats.value.avgPrice = validPrices.reduce((sum, d) => sum + d.avg_price, 0) / validPrices.length
      }
    }
  } catch (e) {
    console.error('加载月度统计失败', e)
  }
}

const loadRegions = async () => {
  try {
    const { data } = await transactionApi.getRegions()
    regions.value = data?.regions || []
  } catch (e) {
    console.error('加载区域列表失败', e)
  }
}

watch(selectedRegion, () => {
  loadPriceTrend()
})

onMounted(async () => {
  initCharts()
  await Promise.all([
    loadRegions(),
    loadPriceTrend(),
    loadRegionStats(),
    loadVolumeTrend(),
    loadMonthlyStats()
  ])
  
  window.addEventListener('resize', () => {
    priceChart?.resize()
    regionChart?.resize()
    volumeChart?.resize()
  })
})
</script>

<style scoped>
.dashboard {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
}
</style>
