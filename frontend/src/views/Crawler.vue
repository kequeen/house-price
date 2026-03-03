<template>
  <div class="crawler">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>链家数据采集</span>
          </template>
          
          <el-form label-width="100px">
            <el-form-item label="选择城市">
              <el-select v-model="selectedCity" placeholder="选择城市" style="width: 100%;">
                <el-option
                  v-for="city in cities"
                  :key="city.code"
                  :label="city.name"
                  :value="city.code"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="指定区域">
              <el-input
                v-model="selectedRegions"
                placeholder="留空采集全部，多个用逗号分隔"
              />
            </el-form-item>
            
            <el-form-item label="每区页数">
              <el-input-number v-model="pagesPerRegion" :min="1" :max="100" />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                @click="startCrawler"
                :loading="crawlerStatus.is_running"
                :disabled="crawlerStatus.is_running"
              >
                {{ crawlerStatus.is_running ? '采集中...' : '开始采集' }}
              </el-button>
            </el-form-item>
          </el-form>
          
          <el-divider />
          
          <div class="status-info">
            <p><strong>状态：</strong>
              <el-tag :type="crawlerStatus.is_running ? 'warning' : 'success'">
                {{ crawlerStatus.is_running ? '运行中' : '空闲' }}
              </el-tag>
            </p>
            <p><strong>上次运行：</strong>{{ crawlerStatus.last_run || '-' }}</p>
            <p><strong>已采集数量：</strong>{{ crawlerStatus.total_crawled }}</p>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>使用说明</span>
            </div>
          </template>
          
          <el-alert
            title="注意事项"
            type="warning"
            :closable="false"
            style="margin-bottom: 20px;"
          >
            <ul style="margin: 0; padding-left: 20px;">
              <li>爬虫采集链家网站的成交数据，仅供学习研究使用</li>
              <li>请遵守网站的robots.txt和使用条款</li>
              <li>建议在非高峰时段运行，避免对网站造成压力</li>
              <li>采集速度已做限制，请勿频繁请求</li>
            </ul>
          </el-alert>
          
          <el-descriptions title="功能说明" :column="1" border>
            <el-descriptions-item label="数据来源">链家网成交记录</el-descriptions-item>
            <el-descriptions-item label="采集内容">
              小区名称、成交日期、成交价格、面积、户型、朝向等
            </el-descriptions-item>
            <el-descriptions-item label="支持城市">
              北京、上海、广州、深圳、杭州、南京、成都、武汉、天津、西安等
            </el-descriptions-item>
            <el-descriptions-item label="数据存储">
              自动保存到本地数据库，可在"成交记录"页面查看
            </el-descriptions-item>
          </el-descriptions>
          
          <el-divider />
          
          <h4>采集流程</h4>
          <el-steps :active="crawlerStatus.is_running ? 2 : 0" finish-status="success">
            <el-step title="选择城市" description="选择要采集的城市" />
            <el-step title="开始采集" description="后台异步采集数据" />
            <el-step title="数据入库" description="自动保存到数据库" />
          </el-steps>
        </el-card>
        
        <el-card style="margin-top: 20px;">
          <template #header>
            <span>API接口说明</span>
          </template>
          
          <el-table :data="apiEndpoints" border style="width: 100%">
            <el-table-column prop="method" label="方法" width="80">
              <template #default="{ row }">
                <el-tag :type="row.method === 'GET' ? 'primary' : 'success'" size="small">
                  {{ row.method }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="endpoint" label="接口" />
            <el-table-column prop="description" label="说明" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { crawlerApi } from '../api'

const selectedCity = ref('bj')
const selectedRegions = ref('')
const pagesPerRegion = ref(3)
const cities = ref([])
const crawlerStatus = ref({
  is_running: false,
  last_run: null,
  total_crawled: 0,
  current_region: null
})

const apiEndpoints = ref([
  { method: 'POST', endpoint: '/api/crawler/start', description: '启动爬虫任务' },
  { method: 'GET', endpoint: '/api/crawler/status', description: '获取爬虫状态' },
  { method: 'GET', endpoint: '/api/crawler/cities', description: '获取支持的城市列表' }
])

let statusInterval = null

const loadCities = async () => {
  try {
    const { data } = await crawlerApi.getCities()
    cities.value = data?.cities || []
  } catch (e) {
    console.error('加载城市失败', e)
  }
}

const loadStatus = async () => {
  try {
    const { data } = await crawlerApi.getStatus()
    crawlerStatus.value = data || {}
  } catch (e) {
    console.error('加载状态失败', e)
  }
}

const startCrawler = async () => {
  try {
    const { data } = await crawlerApi.start(
      selectedCity.value,
      selectedRegions.value,
      pagesPerRegion.value
    )
    ElMessage.success(data.message)
    await loadStatus()
  } catch (e) {
    ElMessage.error('启动失败：' + (e.response?.data?.detail || e.message))
  }
}

onMounted(async () => {
  await loadCities()
  await loadStatus()
  
  statusInterval = setInterval(loadStatus, 3000)
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>

<style scoped>
.crawler {
  width: 100%;
}

.status-info {
  font-size: 14px;
  line-height: 2;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
